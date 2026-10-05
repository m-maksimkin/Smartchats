import { useCallback, useEffect, useRef, useState } from 'react';

import type { ChatMessage, ChatStatus } from './types';

type ServerFrame =
  | { type: 'status'; state: 'indexing' | 'ready' | 'error' }
  | { type: 'delta'; text: string }
  | { type: 'done'; sources: string[] }
  | { type: 'error'; message: string };

function socketUrl(chatUuid: string): string {
  const scheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
  return `${scheme}${window.location.host}/ws/chats/${chatUuid}/`;
}

export function useChatSocket(chatUuid: string) {
  const [status, setStatus] = useState<ChatStatus>('connecting');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [answering, setAnswering] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const nextId = useRef(1);

  const updateLastAssistant = useCallback((update: (message: ChatMessage) => ChatMessage) => {
    setMessages((current) => {
      const last = current[current.length - 1];
      if (!last || last.role !== 'assistant') {
        return current;
      }
      return [...current.slice(0, -1), update(last)];
    });
  }, []);

  useEffect(() => {
    const socket = new WebSocket(socketUrl(chatUuid));
    socketRef.current = socket;

    socket.onmessage = (event: MessageEvent<string>) => {
      const frame = JSON.parse(event.data) as ServerFrame;
      switch (frame.type) {
        case 'status':
          setStatus(frame.state);
          break;
        case 'delta':
          updateLastAssistant((message) => ({ ...message, text: message.text + frame.text }));
          break;
        case 'done':
          updateLastAssistant((message) => ({ ...message, sources: frame.sources, pending: false }));
          setAnswering(false);
          break;
        case 'error':
          updateLastAssistant((message) => ({
            ...message,
            text: message.text || frame.message,
            pending: false,
            failed: true,
          }));
          setAnswering(false);
          break;
      }
    };
    socket.onclose = () => {
      setStatus('closed');
      setAnswering(false);
    };

    return () => {
      socket.onclose = null;
      socket.close();
    };
  }, [chatUuid, updateLastAssistant]);

  const send = useCallback((text: string) => {
    const socket = socketRef.current;
    const trimmed = text.trim();
    if (!socket || socket.readyState !== WebSocket.OPEN || !trimmed) {
      return;
    }
    const userId = nextId.current++;
    const assistantId = nextId.current++;
    setMessages((current) => [
      ...current,
      { id: userId, role: 'user', text: trimmed, sources: [], pending: false, failed: false },
      { id: assistantId, role: 'assistant', text: '', sources: [], pending: true, failed: false },
    ]);
    setAnswering(true);
    socket.send(JSON.stringify({ type: 'message', text: trimmed }));
  }, []);

  const reset = useCallback(() => {
    const socket = socketRef.current;
    setMessages([]);
    setAnswering(false);
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'reset' }));
    }
  }, []);

  return { status, messages, answering, send, reset };
}
