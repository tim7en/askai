import { FileData } from '@/types';

export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result;
      if (typeof result === 'string') {
        resolve(result);
      } else {
        reject(new Error('Failed to read file as text'));
      }
    };
    reader.onerror = () => reject(new Error('File reading failed'));
    reader.readAsText(file);
  });
}

export function isTextFile(file: File): boolean {
  // Check if it's a text file based on type or extension
  const textTypes = [
    'text/',
    'application/json',
    'application/javascript',
    'application/typescript',
    'application/xml',
    'application/yaml',
  ];
  
  const textExtensions = [
    '.txt', '.md', '.js', '.ts', '.jsx', '.tsx', '.css', '.scss', '.sass',
    '.html', '.htm', '.xml', '.json', '.yaml', '.yml', '.csv', '.py',
    '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go', '.rs', '.swift',
    '.kt', '.cs', '.vb', '.sql', '.sh', '.bat', '.ps1', '.dockerfile',
    '.gitignore', '.env', '.config', '.ini', '.cfg', '.log'
  ];

  // Check MIME type
  if (textTypes.some(type => file.type.startsWith(type))) {
    return true;
  }

  // Check file extension
  const fileName = file.name.toLowerCase();
  return textExtensions.some(ext => fileName.endsWith(ext));
}

export async function processFiles(files: FileList): Promise<FileData[]> {
  const fileDataArray: FileData[] = [];
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    
    if (isTextFile(file)) {
      try {
        const content = await readFileAsText(file);
        fileDataArray.push({
          name: file.name,
          content,
          path: file.webkitRelativePath || file.name,
          size: file.size,
          type: file.type || 'text/plain'
        });
      } catch (error) {
        console.error(`Failed to read file ${file.name}:`, error);
      }
    }
  }
  
  return fileDataArray;
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
