import asyncio
import os
import uuid

from dotenv import load_dotenv

load_dotenv()

# Set PYTHONPATH
import sys

sys.path.append(os.path.join(os.getcwd(), "core", "src"))

from ora_core.api.schemas.messages import ContextBinding, MessageRequest, UserIdentity
from ora_core.brain.process import MainProcess
from ora_core.database.repo import Repository
from ora_core.database.session import AsyncSessionLocal


async def debug_post_message():
    async with AsyncSessionLocal() as db:
        repo = Repository(db)
        
        req = MessageRequest(
            user_identity=UserIdentity(provider="discord", id="test-user-123", display_name="Tester"),
            content="Hello Brain",
            idempotency_key=str(uuid.uuid4()),
            context_binding=ContextBinding(provider="discord", kind="dm", external_id="dm:test-user-123"),
            stream=True
        )
        
        print("--- Debug 1: User Resolution ---")
        user = await repo.get_or_create_user(
            provider=req.user_identity.provider,
            provider_id=req.user_identity.id,
            display_name=req.user_identity.display_name
        )
        print(f"User resolved: {user.id}")

        print("--- Debug 2: Conversation Resolution ---")
        conv_id = await repo.resolve_conversation(
            user_id=user.id,
            conversation_id=req.conversation_id,
            context_binding=req.context_binding.model_dump() if req.context_binding else None
        )
        print(f"Conv resolved: {conv_id}")

        print("--- Debug 3: Message & Run Creation ---")
        att_dicts = [a.model_dump() for a in req.attachments]
        msg, run = await repo.create_user_message_and_run(
            conversation_id=conv_id,
            user_id=user.id,
            content=req.content,
            attachments=att_dicts,
            idempotency_key=req.idempotency_key
        )
        print(f"Message ID: {msg.id}, Run ID: {run.id}")

        print("--- Debug 4: Brain Initialiation ---")
        # Just init, don't run yet
        MainProcess(run.id, conv_id, req, db)
        print("Brain initialized.")

        # Note: We won't call brain.run() here as it might try to call real APIs
        # But we've reached the point where the 500 would likely have occurred in the route.

if __name__ == "__main__":
    asyncio.run(debug_post_message())
