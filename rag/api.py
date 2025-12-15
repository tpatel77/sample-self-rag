"""
FastAPI server for RAG Document Processing.
Exposes an endpoint to process documents using the ADK workflow framework.
"""

import json
from typing import Any, Union
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import WorkflowOrchestrator
from .onboarding_api import router as onboarding_router

from .onboarding_api import router as onboarding_router, db

app = FastAPI(
    title="RAG Document Processor",
    description="API for processing documents using ADK workflows",
    version="1.0.0"
)

# Include the onboarding/onfiguration endpoints
app.include_router(onboarding_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    await db.connect()
    # Initialize Schema
    try:
        schema_path = Path(__file__).parent.parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            # asyncpg execute can handle multiple statements if simple, but fetch/execute might splitting issues.
            # Using execute for script
            await db.execute(schema_sql)
            print("Schema initialized.")
    except Exception as e:
        print(f"Warning: Schema initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

# Path to the workflow YAML
WORKFLOW_PATH = Path(__file__).parent / "document_processor.yaml"


class DocumentRequest(BaseModel):
    """Request model for document processing."""
    document: Union[str, dict[str, Any]] = Field(
        ..., 
        description="Document content - can be a string or JSON object"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata as JSON"
    )


class DocumentResponse(BaseModel):
    """Response model for document processing."""
    status: str
    session_id: str
    result: str
    state: dict[str, Any] = Field(default_factory=dict)


@app.post("/process", response_model=DocumentResponse)
async def process_document(request: DocumentRequest):
    """
    Process a document using the document_processor workflow.
    
    Args:
        request: DocumentRequest containing document and metadata
        
    Returns:
        DocumentResponse with processing results
    """
    try:
        # Convert document to string if it's a dict
        if isinstance(request.document, dict):
            document_str = json.dumps(request.document)
        else:
            document_str = request.document
            
        # Create user input combining document and metadata
        user_input = f"Document: {document_str}\nMetadata: {json.dumps(request.metadata)}"
        
        # Initialize orchestrator and load workflow
        orchestrator = WorkflowOrchestrator(app_name="rag_processor")
        orchestrator.load_workflow(str(WORKFLOW_PATH))
        
        # Generate unique session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Run the workflow
        result = await orchestrator.run_async(
            user_input=user_input,
            session_id=session_id,
            initial_state={
                "document": document_str,
                "metadata": request.metadata
            }
        )
        
        # Get final state from session
        final_state = {}
        if orchestrator._session_service:
            try:
                session = await orchestrator._session_service.get_session(
                    app_name="rag_processor", 
                    user_id="default_user", 
                    session_id=session_id
                )
                if session:
                    final_state = session.state
            except Exception:
                # Some session services may not support get_session after run
                pass
        
        return DocumentResponse(
            status="success",
            session_id=session_id,
            result=result,
            state=final_state
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
