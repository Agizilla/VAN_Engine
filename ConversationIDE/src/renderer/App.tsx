import React, { useEffect, useState } from 'react';
import { ChatPanel } from './components/Chat/ChatPanel';
import { FileTree } from './components/Files/FileTree';
import { Editor } from './components/Files/Editor';
import { StatusBar } from './components/Status/StatusBar';
import { ISOPanel } from './components/Status/ISOPanel';
import { CriteriaPanel } from './components/Status/CriteriaPanel';
import { AlgorithmPanel } from './components/Algorithm/AlgorithmPanel';
import { VoiceTestPanel } from './components/VoiceTest/VoiceTestPanel';
import { InferencePanel } from './components/Inference/InferencePanel';
import { TranscriptViewer } from './components/Transcript/TranscriptViewer';
import { PipelineMonitor } from './components/Monitor/PipelineMonitor';
import { SkillCustomization } from './components/Settings/SkillCustomization';
import { useISOStore } from './store/isoStore';
import { useFileStore } from './store/fileStore';
import { initPhaseListener } from './store/phaseStore';

type SidebarTab = 'files' | 'iso' | 'criteria' | 'algorithm' | 'voice' | 'inference' | 'transcript' | 'monitor' | 'skill';

const App: React.FC = () => {
  const { loadRules } = useISOStore();
  const { setActiveFile } = useFileStore();
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>('files');

  useEffect(() => {
    loadRules();
    initPhaseListener();
  }, []);

  const handleFileSelect = (path: string) => {
    setSelectedFilePath(path);
    const tree = useFileStore.getState().tree;
    const findNode = (node: any): any => {
      if (!node) return null;
      if (node.path === path) return node;
      if (node.children) {
        for (const child of node.children) {
          const found = findNode(child);
          if (found) return found;
        }
      }
      return null;
    };
    const node = findNode(tree);
    if (node) {
      setActiveFile(node);
    }
  };

  const renderSidebarContent = () => {
    switch (sidebarTab) {
      case 'files':
        return (
          <>
            <FileTree rootPath={'.'} onFileSelect={handleFileSelect} />
            <Editor />
          </>
        );
      case 'iso':
        return <ISOPanel />;
      case 'criteria':
        return <CriteriaPanel />;
      case 'algorithm':
        return <AlgorithmPanel />;
      case 'voice':
        return <VoiceTestPanel />;
      case 'inference':
        return <InferencePanel />;
      case 'transcript':
        return <TranscriptViewer />;
      case 'monitor':
        return <PipelineMonitor />;
      case 'skill':
        return <SkillCustomization />;
    }
  };

  return (
    <div className="app-layout">
      <div className="sidebar">
        <div className="sidebar-tabs">
          <button
            className={`sidebar-tab ${sidebarTab === 'files' ? 'active' : ''}`}
            onClick={() => setSidebarTab('files')}
          >Files</button>
          <button
            className={`sidebar-tab ${sidebarTab === 'iso' ? 'active' : ''}`}
            onClick={() => setSidebarTab('iso')}
          >ISO</button>
          <button
            className={`sidebar-tab ${sidebarTab === 'criteria' ? 'active' : ''}`}
            onClick={() => setSidebarTab('criteria')}
          >Criteria</button>
          <button
            className={`sidebar-tab ${sidebarTab === 'algorithm' ? 'active' : ''}`}
            onClick={() => setSidebarTab('algorithm')}
          >Algorithm</button>
          <button
            className={`sidebar-tab ${sidebarTab === 'voice' ? 'active' : ''}`}
            onClick={() => setSidebarTab('voice')}
          >Voice</button>
          <button
            className={`sidebar-tab ${sidebarTab === 'inference' ? 'active' : ''}`}
            onClick={() => setSidebarTab('inference')}
          >Infer</button>
          <button
            className={`sidebar-tab ${sidebarTab === 'transcript' ? 'active' : ''}`}
            onClick={() => setSidebarTab('transcript')}
          >Transcript</button>
          <button
            className={`sidebar-tab ${sidebarTab === 'monitor' ? 'active' : ''}`}
            onClick={() => setSidebarTab('monitor')}
          >Monitor</button>
          <button
            className={`sidebar-tab ${sidebarTab === 'skill' ? 'active' : ''}`}
            onClick={() => setSidebarTab('skill')}
          >Skills</button>
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {renderSidebarContent()}
        </div>
      </div>
      <div className="main-content">
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <ChatPanel />
        </div>
        <StatusBar />
      </div>
    </div>
  );
};

export default App;
