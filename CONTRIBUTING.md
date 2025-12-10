🤝 Contributing to the HCAM Knowledge Graph™

Thank you for your interest in contributing!

This project follows a structured approach to ensure consistency, accuracy, and high-quality glossary data across Hindi, English, and Hinglish formats.

Please read this guide carefully before submitting a contribution.

📌 Contribution Workflow

1. Fork the Repository

Create a personal copy of the repository by clicking Fork.

This allows you to make changes without affecting the main project.

2. Create a New Term Using the HCAM Pattern
All glossary entries must follow the standardized HCAM JSON Structure, including:
•	Unique id

•	domain

•	pillar

•	topic_cluster

•	label_en, label_hi, label_hiLatn

•	Definitions (EN, HI, Hinglish)

•	Mental anchor example

•	Tags (if applicable)

Please refer to the /schema/ folder or existing examples for the exact format.

3. Submit a Pull Request (PR)

Once your term is added and tested locally:
1.	Push changes to your fork
2.	Open a Pull Request targeting the main branch

Your PR will automatically trigger the JSON Validation Workflow, which checks:

•	Schema compliance

•	ID uniqueness

•	Required fields

•	Correct formatting

•	Valid JSON syntax

You will see pass/fail results in your PR automatically.

4. Review & Merge

After validation:

•	Maintainers review your entry

•	If approved, your PR is merged into the main branch

Once merged, your contribution becomes part of:

•	GitHub raw data

•	Public JSON datasets

•	Any connected schema-driven web pages or APIs

5. Access Your Term (Download Link)

All validated glossary files are automatically available via:

https://raw.githubusercontent.com/<org>/<repo>/main/data/glossary.json

or other download endpoints listed in the repository README.

This ensures your contribution is instantly usable by developers, educators, and AI systems consuming the HCAM dataset.

Contribution Guidelines

✅ Follow the exact field names and structure

Do not rename keys or introduce custom fields unless approved.

✅ Use clear, concise definitions

Avoid subjective or promotional language.

✅ Maintain tone consistency

The project uses an educational, exam-friendly tone suited for BFSI and AI literacy learners.

✅ Provide a practical "mental anchor"

Always include a relatable real-life example.

✅ Add Hinglish transliteration (label_hiLatn)

Follow simple phonetic transliteration.

🛠 Recommended Tools

•	VS Code with JSON schema validation

•	jsonlint or VS Code built-in formatter

•	GitHub Desktop (optional)

❓ Need Help?

If you are unsure about structure, naming, or domain classification:

•	Open an Issue

•	Tag it as question, schema, or guidance

We’re here to help you contribute smoothly.

👏 Thank You

Your contributions help expand the HCAM Knowledge Graph™ and make BFSI + AI Literacy accessible to learners across India and beyond.

