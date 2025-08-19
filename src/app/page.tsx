import FileUpload from '@/components/FileUpload';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI File Analyzer
          </h1>
          <p className="text-xl text-gray-600">
            Upload files or folders and get AI-powered analysis reports
          </p>
        </div>
        <FileUpload />
      </div>
    </main>
  );
}
