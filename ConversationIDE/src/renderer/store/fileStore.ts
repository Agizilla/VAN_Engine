import { create } from 'zustand';

export interface FileNode {
  path: string;
  name: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  content?: string;
  size?: number;
  modified: number;
  isWatched: boolean;
  iso_004_compliant?: boolean;
}

interface FileState {
  tree: FileNode | null;
  activeFile: FileNode | null;
  activeFileContent: string | null;
  watchedPaths: string[];
  isLoading: boolean;

  loadTree: (rootPath: string) => Promise<void>;
  setActiveFile: (node: FileNode) => void;
  setActiveFileContent: (content: string) => void;
  readFile: (filePath: string) => Promise<string>;
  writeFile: (filePath: string, content: string) => Promise<void>;
  createFile: (parentPath: string, fileName: string) => Promise<void>;
  deleteFile: (filePath: string) => Promise<void>;
  setLoading: (loading: boolean) => void;
}

let fileCounter = 0;

export const useFileStore = create<FileState>((set, get) => ({
  tree: null,
  activeFile: null,
  activeFileContent: null,
  watchedPaths: [],
  isLoading: false,

  loadTree: async (rootPath: string) => {
    set({ isLoading: true });
    try {
      const api = (window as any).electronAPI;
      if (api?.files?.tree) {
        const tree = await api.files.tree(rootPath);
        set({ tree, isLoading: false });
      }
    } catch {
      set({ isLoading: false });
    }
  },

  setActiveFile: (node) => {
    set({ activeFile: node });
    if (node.type === 'file') {
      get().readFile(node.path).then(content => {
        set({ activeFileContent: content });
      });
    }
  },

  setActiveFileContent: (content) => {
    set({ activeFileContent: content });
  },

  readFile: async (filePath: string) => {
    try {
      const api = (window as any).electronAPI;
      if (api?.files?.read) {
        const result = await api.files.read(filePath);
        return result.content;
      }
    } catch {
      return '';
    }
    return '';
  },

  writeFile: async (filePath: string, content: string) => {
    try {
      const api = (window as any).electronAPI;
      if (api?.files?.write) {
        await api.files.write(filePath, content);
      }
    } catch { }
  },

  createFile: async (parentPath: string, fileName: string) => {
    const filePath = `${parentPath}/${fileName}`;
    try {
      const api = (window as any).electronAPI;
      if (api?.files?.write) {
        await api.files.write(filePath, '');
      }
      await get().loadTree(parentPath);
    } catch { }
  },

  deleteFile: async (filePath: string) => {
    try {
      const api = (window as any).electronAPI;
      if (api?.files?.delete) {
        await api.files.delete(filePath);
      }
      const tree = get().tree;
      if (tree) {
        await get().loadTree(tree.path);
      }
    } catch { }
  },

  setLoading: (loading) => set({ isLoading: loading })
}));
