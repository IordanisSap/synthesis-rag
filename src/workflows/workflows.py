
from src.workflows.blocks.detect_relevant_classes import detect_relevant_classes
from src.workflows.blocks.generate_class_descriptions import generate_class_descriptions, get_class_contexts
from src.workflows.blocks.generate_xquery import generate_xquery
from src.workflows.blocks.get_field_descriptions import get_class_field_descriptions, build_field_descriptions

from src.index.index import save_to_index, load_from_index
from src.xquery.build_context import build_class_xquery_context
from src.xquery.postprocessing import postprocess_xquery

from src.db import ExistDB

def workflow1(question: str, db: ExistDB, workdir: str, config: dict, index_folder: str):
    descs = load_from_index("class_descriptions", workdir.split("/")[-1], index_folder)
    if not descs:
        descs = generate_class_descriptions(db, workdir, config["generation"])
        save_to_index("class_descriptions", descs, workdir.split("/")[-1], index_folder)



    relevant_classes = detect_relevant_classes(
        question=question,
        class_descriptions=descs,
        llm_config=config["generation"]
    )



    contexts = get_class_contexts(db, workdir, classes=relevant_classes)
    xquery = generate_xquery(context="\n".join([build_class_xquery_context(context) for context in contexts]), 
                            question=question, 
                            llm_config=config["generation"])

    print(f"Raw XQuery:\n{xquery}\n")
    xquery = postprocess_xquery(xquery, config["database"])
    print(f"Postprocessed XQuery:\n{xquery}\n")
    print(db.execute_xquery(xquery))



def workflow2(question: str, db: ExistDB, workdir: str, config: dict, index_folder: str):
    # class_descriptions = load_from_index("class_descriptions", workdir.split("/")[-1], index_folder)
    # if not class_descriptions:
    #     class_descriptions = generate_class_descriptions(db, workdir, config["generation"])
    #     save_to_index("class_descriptions", class_descriptions, workdir.split("/")[-1], index_folder)

    field_descriptions = load_from_index("field_descriptions", workdir.split("/")[-1], index_folder)
    if not field_descriptions:
        field_descriptions = build_field_descriptions(db, workdir)
        save_to_index("field_descriptions", field_descriptions, workdir.split("/")[-1], index_folder)


    # relevant_classes = ['Organization', 'Person']
    print(get_class_field_descriptions(field_descriptions, 'Organization'))
    print()
    print(get_class_field_descriptions(field_descriptions, 'Person'))