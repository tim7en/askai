# AI File Analyzer

A Next.js web application that allows users to upload files or folders and generate AI-powered analysis reports based on custom prompts using the Z.AI API (GLM-4-32B model).

## Features

- 📁 **File & Folder Upload**: Upload individual files or entire folders for analysis
- 🤖 **AI-Powered Analysis**: Uses Z.AI's GLM-4-32B model for intelligent file analysis
- 📝 **Custom Prompts**: Write custom analysis prompts to get specific insights
- 📊 **Detailed Reports**: Get comprehensive analysis reports for each file
- 🎨 **Modern UI**: Clean, responsive interface built with Tailwind CSS
- ⚡ **Fast Processing**: Efficient file processing and analysis

## Tech Stack

- **Frontend**: Next.js 15 with TypeScript
- **Styling**: Tailwind CSS
- **AI Provider**: Z.AI API (GLM-4-32B model)
- **File Handling**: Custom file processing utilities
- **Deployment**: Vercel-ready

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Z.AI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd askai
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
Create a `.env.local` file in the root directory:
```env
ZAI_API_KEY=your_zai_api_key_here
ZAI_API_URL=https://api.z.ai/v1/chat/completions
```

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. **Upload Files**: 
   - Use the "Select Files" button to upload individual files
   - Use the "Select Folder" button to upload an entire folder

2. **Write Analysis Prompt**: 
   - Enter a detailed prompt describing what you want to analyze
   - Examples:
     - "Analyze the code quality and suggest improvements"
     - "Summarize the main functions and their purposes"
     - "Find potential security issues"
     - "Explain the project structure and dependencies"

3. **Generate Report**: 
   - Click "Analyze Files" to start the AI analysis
   - Wait for the AI to process each file
   - Review the detailed analysis reports

## Supported File Types

The application automatically detects and processes text-based files including:

- Code files: `.js`, `.ts`, `.jsx`, `.tsx`, `.py`, `.java`, `.cpp`, `.c`, `.php`, `.rb`, `.go`, `.rs`, `.swift`, `.kt`, `.cs`
- Web files: `.html`, `.css`, `.scss`, `.sass`, `.xml`
- Data files: `.json`, `.yaml`, `.yml`, `.csv`, `.sql`
- Documentation: `.md`, `.txt`, `.log`
- Configuration: `.env`, `.config`, `.ini`, `.cfg`, `.dockerfile`

## API Endpoints

### POST /api/analyze

Analyzes uploaded files using the Z.AI API.

**Request Body:**
```json
{
  "files": [
    {
      "name": "example.js",
      "content": "file content here",
      "path": "src/example.js",
      "size": 1024,
      "type": "application/javascript"
    }
  ],
  "prompt": "Analyze this code for quality issues"
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "fileName": "example.js",
      "filePath": "src/example.js",
      "analysis": "AI analysis result here...",
      "metadata": {
        "size": 1024,
        "type": "application/javascript"
      }
    }
  ],
  "message": "Successfully analyzed 1 files"
}
```

## Project Structure

```
src/
├── app/
│   ├── api/
│   │   └── analyze/
│   │       └── route.ts          # API endpoint for file analysis
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Home page
├── components/
│   └── FileUpload.tsx            # Main file upload and analysis component
├── lib/
│   ├── file-utils.ts             # File processing utilities
│   └── zai-client.ts             # Z.AI API client
└── types/
    └── index.ts                  # TypeScript type definitions
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ZAI_API_KEY` | Your Z.AI API key for GLM-4-32B model | Yes |
| `ZAI_API_URL` | Z.AI API endpoint URL | Yes |

## Deployment

The application is ready for deployment on Vercel:

1. Push your code to a Git repository
2. Connect your repository to Vercel
3. Set the environment variables in Vercel dashboard
4. Deploy

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the GitHub repository.
