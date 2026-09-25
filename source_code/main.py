from pathlib import Path
from fastapi.responses import FileResponse
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from source_code.database.postgres import get_connection
from source_code.rag_service import retrieve_context
from source_code.local_answer_service import generate_local_answer
from source_code.upload_service import process_uploaded_paper
from source_code.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from source_code.kafka_service import publish_paper_uploaded

app = FastAPI(
    title="SmartResearch Hub",
    description="AI-powered semantic research paper repository",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


security = HTTPBearer()


# --------------------------------------------------
# Request models
# --------------------------------------------------

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


class LoginRequest(BaseModel):
    username: str
    password: str


# --------------------------------------------------
# Authentication helpers
# --------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        return decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )


def require_admin(current_user=Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    return current_user


# --------------------------------------------------
# Basic API
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "SmartResearch Hub API is running",
        "status": "success",
    }


# --------------------------------------------------
# Register
# --------------------------------------------------

@app.post("/register")
def register(request: RegisterRequest):

    if request.role not in ["user", "admin"]:
        raise HTTPException(
            status_code=400,
            detail="Role must be user or admin.",
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = %s;",
        (request.username,),
    )

    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Username already exists.",
        )

    password_hash = hash_password(request.password)

    cursor.execute(
        """
        INSERT INTO users (username, password_hash, role)
        VALUES (%s, %s, %s)
        RETURNING id, username, role;
        """,
        (
            request.username,
            password_hash,
            request.role,
        ),
    )

    user = cursor.fetchone()

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "User registered successfully.",
        "user": {
            "id": user[0],
            "username": user[1],
            "role": user[2],
        },
    }


# --------------------------------------------------
# Login
# --------------------------------------------------

@app.post("/login")
def login(request: LoginRequest):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, username, password_hash, role
        FROM users
        WHERE username = %s;
        """,
        (request.username,),
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    if not verify_password(
        request.password,
        user[2],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    token = create_access_token(
        username=user[1],
        role=user[3],
    )

    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user[0],
            "username": user[1],
            "role": user[3],
        },
    }


# --------------------------------------------------
# Current user
# --------------------------------------------------

@app.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "message": "Authenticated user.",
        "user": current_user,
    }


# --------------------------------------------------
# Papers
# --------------------------------------------------

@app.get("/papers")
def get_papers():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, authors, domain, year, created_at
        FROM papers
        ORDER BY id;
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    papers = []

    for row in rows:
        papers.append(
            {
                "id": row[0],
                "title": row[1],
                "authors": row[2],
                "domain": row[3],
                "year": row[4],
                "created_at": row[5],
            }
        )

    return {
        "count": len(papers),
        "papers": papers,
    }
@app.get("/papers/{paper_id}/pdf")
def get_paper_pdf(paper_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, domain
        FROM papers
        WHERE id = %s;
        """,
        (paper_id,),
    )

    paper = cursor.fetchone()

    cursor.close()
    connection.close()

    if not paper:
        raise HTTPException(
            status_code=404,
            detail="Paper not found.",
        )

    paper_id, title, domain = paper

    # Search the dataset folders for the corresponding PDF.
    project_root = Path(__file__).resolve().parent.parent

    search_directories = [
        project_root / "dataset" / "DBMS",
        project_root / "dataset" / "DS",
        project_root / "dataset" / "ES",
        project_root / "dataset" / "ML",
        project_root / "dataset" / "OS",
        project_root / "dataset" / "uploads",
    ]

    # First try to match the paper using its database title.
    possible_names = {
        title,
        title.replace("/", "_"),
    }

    for directory in search_directories:
        if not directory.exists():
            continue

        for pdf_file in directory.glob("*.pdf"):
            if pdf_file.stem in possible_names:
                return FileResponse(
                    path=str(pdf_file),
                    media_type="application/pdf",
                    filename=pdf_file.name,
                )

    # For the current dataset, paper titles are often filenames such as
    # ML10, DBMS5, DS7, etc. Use the domain + paper order as a fallback.
    domain_folder = project_root / "dataset" / str(domain)

    if domain_folder.exists():
        pdf_files = sorted(domain_folder.glob("*.pdf"))

        # Try an exact filename match such as ML10 / DBMS5.
        for pdf_file in pdf_files:
            if pdf_file.stem.lower() == title.lower():
                return FileResponse(
                    path=str(pdf_file),
                    media_type="application/pdf",
                    filename=pdf_file.name,
                )

    raise HTTPException(
        status_code=404,
        detail="PDF file for this paper could not be located.",
    )


# --------------------------------------------------
# Semantic search
# --------------------------------------------------

@app.post("/search")
def search(request: SearchRequest):

    from source_code.semantic_search import search_papers

    results = search_papers(
        request.query,
        top_k=request.top_k,
    )

    formatted_results = []

    for result in results:

        (
            paper_id,
            title,
            domain,
            year,
            chunk_index,
            content,
            similarity,
        ) = result

        formatted_results.append(
            {
                "paper_id": paper_id,
                "title": title,
                "domain": domain,
                "year": year,
                "best_chunk": chunk_index,
                "similarity": round(
                    float(similarity),
                    4,
                ),
                "content": content[:1000],
            }
        )

    return {
        "query": request.query,
        "count": len(formatted_results),
        "results": formatted_results,
    }


# --------------------------------------------------
# RAG / Ask
# --------------------------------------------------

@app.post("/ask")
def ask_question(request: AskRequest):

    result = retrieve_context(
        request.question,
        top_k=request.top_k,
    )

    answer = generate_local_answer(
        request.question,
        result["context"],
    )

    return {
        "question": request.question,
        "answer": answer,
        "sources": result["sources"],
        "context": result["context"],
    }


# --------------------------------------------------
# Admin-only paper upload
# --------------------------------------------------

@app.post("/papers/upload")
async def upload_paper(
    file: UploadFile = File(...),
    title: str = Form(...),
    authors: str = Form(""),
    domain: str = Form(""),
    year: int | None = Form(None),
current_user: dict = Depends(get_current_user),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    upload_dir = Path("dataset/uploads")
    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = upload_dir / file.filename

    file_content = await file.read()

    with open(file_path, "wb") as output_file:
        output_file.write(file_content)

    try:

        result = process_uploaded_paper(
            str(file_path),
            title,
            authors,
            domain,
            year,
        )
        publish_paper_uploaded(
            {
                "paper_id": result.get("paper_id"),
                "title": title,
                "domain": domain,
                "year": year,
                "uploaded_by": current_user["username"],
            }
        )

        return {
            "message": "Paper uploaded and processed successfully.",
            "uploaded_by": current_user["username"],
            "result": result,
        }

    except Exception as error:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )