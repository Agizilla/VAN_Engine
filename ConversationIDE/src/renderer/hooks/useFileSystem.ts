import { useEffect, useCallback } from 'react';
import { useFileStore } from '../store/fileStore';

export function useFileSystem(initialPath?: string) {
  const {
    tree,
    activeFile,
    activeFileContent,
    isLoading,
    loadTree,
    setActiveFile,
    readFile,
    writeFile,
    createFile,
    deleteFile
  } = useFileStore();

  useEffect(() => {
    if (initialPath) {
      loadTree(initialPath);
    }
  }, [initialPath]);

  useEffect(() => {
    const api = (window as any).electronAPI;
    if (api?.files?.onChanged) {
      api.files.onChanged((data: any) => {
        if (initialPath) {
          loadTree(initialPath);
        }
      });
    }
  }, [initialPath]);

  const saveFile = useCallback(async (content: string) => {
    if (activeFile) {
      await writeFile(activeFile.path, content);
    }
  }, [activeFile]);

  return {
    tree,
    activeFile,
    activeFileContent,
    isLoading,
    loadTree,
    setActiveFile,
    readFile,
    saveFile,
    createFile,
    deleteFile
  };
}
