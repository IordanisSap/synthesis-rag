
from src.workflows.blocks.generate_class_descriptions import generate_class_descriptions, get_class_examples, fill_class_context_fields
from src.workflows.blocks.generate_xquery import generate_xquery
from src.workflows.blocks.get_field_descriptions import build_field_descriptions

from src.services.ai.tools import detect_relevant_classes
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



    contexts = get_class_examples(db, workdir, classes=relevant_classes)
    xquery = generate_xquery(context="\n".join([build_class_xquery_context(context) for context in contexts]), 
                            question=question, 
                            llm_config=config["generation"])

    print(f"Raw XQuery:\n{xquery}\n")
    xquery = postprocess_xquery(xquery, config["database"])
    print(f"Postprocessed XQuery:\n{xquery}\n")
    print(db.execute_xquery(xquery))



def workflow2(question: str, db: ExistDB, workdir: str, config: dict, index_folder: str):
    class_descriptions = load_from_index("class_descriptions", workdir.split("/")[-1], index_folder)
    if not class_descriptions:
        class_descriptions = generate_class_descriptions(db, workdir, config["generation"])
        save_to_index("class_descriptions", class_descriptions, workdir.split("/")[-1], index_folder)

    field_descriptions = load_from_index("field_descriptions", workdir.split("/")[-1], index_folder)
    if not field_descriptions:
        field_descriptions = build_field_descriptions(db, workdir)
        save_to_index("field_descriptions", field_descriptions, workdir.split("/")[-1], index_folder)



    relevant_classes = detect_relevant_classes(
        question=question,
        class_descriptions=class_descriptions,
        llm_config=config["generation"]
    )

    print(relevant_classes)
    contexts = get_class_examples(db, workdir, classes=relevant_classes)
    print(len(contexts))

    contexts = [fill_class_context_fields(context, field_descriptions) for context in contexts]

    for context in contexts:
        print(f"Class: {context.name}")
        print(f"Template: {context.template}")
        print(f"Example Instances: {context.example_instances}")
        print(f"Field Descriptions: {context.field_descriptions}")
        print("\n")