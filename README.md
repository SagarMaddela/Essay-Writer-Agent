# Essay Writer AI

Essay Writer AI is an interactive web application that generates high-quality essays on any topic, using advanced AI planning, research, drafting, and critique steps. The app provides a transparent, step-by-step process, allowing users to watch how the AI plans, researches, writes, and improves essays in real time.

## Features

- **Live Agent Steps:** See each stage of essay creation, including planning, research, drafting, and critique.
- **Automated Research:** Integrates with external research tools to gather relevant information for essays and revisions.
- **Iterative Improvement:** Supports multiple revision cycles, with AI-generated critiques and improvements.
- **Customizable:** Users can specify the essay topic and the number of allowed revision cycles.
- **Modern UI:** Built with Streamlit for a clean, interactive user experience.

## How It Works

1. **User Input:** Enter your essay topic and select the number of revision cycles.
2. **Planning:** The AI generates a high-level outline for the essay.
3. **Research:** The AI performs automated research to gather supporting information.
4. **Drafting:** The AI writes a full essay based on the plan and research.
5. **Critique & Revision:** The AI critiques its own draft and iteratively improves it, up to the specified number of revisions.
6. **Final Output:** The final essay and critique are displayed for the user.

## Technologies Used

- **Python 3**
- **Streamlit** for the web interface
- **LangGraph** and **LangChain** for agent orchestration
- **ChatGroq** (Llama 3.1-8B-Instant) for language generation
- **Tavily** for automated research
- **Pydantic** for data validation
- **dotenv** for environment variable management

## Setup Instructions

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd Essay_writer
   ```
2. **Create and activate a virtual environment (optional but recommended):**
   ```sh
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set up environment variables:**
   - Create a `.env` file in the project root.
   - Add your API keys (e.g., `TAVILY_API_KEY`) as needed.

5. **Run the application:**
   ```sh
   streamlit run main.py
   ```

## Usage

- Enter your essay topic or prompt in the provided text area.
- Select the number of allowed revisions (1-5).
- Click "Generate Essay" to start the process.
- Watch each step as the AI plans, researches, drafts, and critiques your essay.
- View the final essay and critique at the end of the process.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [Streamlit](https://streamlit.io/)
- [Tavily](https://tavily.com/)
- [Groq](https://groq.com/)

---

For questions or contributions, please open an issue or submit a pull request.