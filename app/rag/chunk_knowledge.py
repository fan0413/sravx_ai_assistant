from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import (MarkdownHeaderTextSplitter,RecursiveCharacterTextSplitter)



def split_markdown(file_path:Path):
    text=file_path.read_text(encoding='utf-8')

    #按章节划分，保留标题信息
    header_slitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#","一级标题"),
            ("##","二级标题"),
            ("###","三级标题")
        ],
        strip_headers=False,
    )
    sections = header_slitter.split_text(text)

    #拆分过长章节
    text_slitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", "。", "；", "！", "？", " ", ""]
    )
    chunks =[]
    for section in sections:
        lines = section.page_content.splitlines()
        #识别表格
        has_table=any(
            line.strip().startswith("|")
            and line.strip().endswith("|")
            for line in lines
        )
        if has_table:
            section_chunks =[section]
        else:
            section_chunks =text_slitter.split_documents([section])

        title_path=">".join(
            section.metadata[key]
            for key in ["一级标题", "二级标题", "三级标题"]
            if key in section.metadata
        )


        for chunk in section_chunks:
            if title_path:
                chunk.page_content = (
                    f"主题：{title_path}\n\n"
                    f"{chunk.page_content}"
                )

        chunks.extend(section_chunks)
    for index,chunk in enumerate(chunks):
        chunk.metadata["source"]=file_path.name
        chunk.metadata["chunk_index"]=index

    return chunks


if __name__=="__main__":
    project_root=Path(__file__).resolve().parent.parent.parent

    file_path=project_root / "knowledge" / "02宠物美容剪刀与工具"/"宠物美容剪刀.md"

    chunks=split_markdown(file_path)

    for index,chunk in enumerate(chunks):
        print(f"\n===== 片段 {index + 1} =====")
        print("字符数：", len(chunk.page_content))
        print("来源信息：", chunk.metadata)
        print(chunk.page_content)