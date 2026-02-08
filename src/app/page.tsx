import Chat from '@/components/Chat';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-1">
            AskAI
          </h1>
          <p className="text-sm text-gray-500">
            Chat with ChatGPT &amp; Claude — powered by multiple AI providers
          </p>
        </div>
        <Chat />
      </div>
    </main>
  );
}
