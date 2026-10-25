import asyncio
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.rag.chunk_knowledge import split_markdown
from app.rag.engine import create_knowledge_engine
from app.rag.knowledge import create_knowledge_store


def import_markdown(file_path:Path,project_root:Path):

    chunks=split_markdown(file_path)

    if not chunks:
        print("无可入库的片段")
        return

    source=file_path.relative_to(project_root).as_posix()
    ids=[]

    for chunk in chunks:
        chunk.metadata["source"]=source

        identify=f"{source}\n{chunk.page_content}"
        chunk_id=str(uuid5(NAMESPACE_URL, identify))
        ids.append(chunk_id)
    engine=create_knowledge_engine()

    try:
        store=create_knowledge_store(engine)

        saved_ids=store.add_documents(
            documents=chunks,
            ids=ids,
        )
        print(f"写入完成：{len(saved_ids)} 个片段")

    finally:
        asyncio.run(engine.close())


if __name__ == "__main__":
    engine = create_knowledge_engine()

    try:
        store = create_knowledge_store(engine)

        results = store.similarity_search(
            "China 440C和440C有什么区别？",
            k=3,
        )

        for index, document in enumerate(results, start=1):
            print(f"\n检索结果 {index}")
            print("来源：", document.metadata)
            print(document.page_content)
    finally:
        asyncio.run(engine.close())