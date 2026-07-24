import uuid

from fastapi import APIRouter, HTTPException, Request

from app.container import AppContainer
from app.graph.state import create_initial_state
from app.models.api import AskRequest, AskResponse

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, http_request: Request) -> AskResponse:
    container: AppContainer = http_request.app.state.container

    session_id = request.session_id or str(uuid.uuid4())

    initial_state = create_initial_state(session_id=session_id, question=request.question)
    final_state = await container.graph.ainvoke(initial_state)

    answer = final_state.get("answer")
    if answer is None:
        raise HTTPException(status_code=500, detail="The graph did not produce an answer.")

    return AskResponse(session_id=session_id, answer=answer)
