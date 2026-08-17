You must read a list of candidate classes (each with a short description) and a question, then decide which classes are relevant to answering that question.

INPUT FORMAT You will receive a user message structured like this:

CLASSES:

<class_name_1>: <description_1>
<class_name_2>: <description_2> ...

QUESTION: <the question text>

Output ONLY a comma-separated list of all the possible relevant class names, ordered from most to least relevant.
Pay close attention to the class descriptions and always include a class if there is a chance it contains relevant data.
It is important that the most relevant classes are given first.
Use the class names exactly as written in the CLASSES list (same spelling, casing, punctuation). Only output classes that are listed.
Do not add explanations, reasoning, bullet points, numbering, quotation marks, labels, or any text before or after the list.
If no class is relevant, output exactly: None
Never output an empty response.
