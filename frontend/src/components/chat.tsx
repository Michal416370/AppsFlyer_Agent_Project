import { useState, useEffect, useRef } from "react";
import { UIRenderer } from "./uiRenderer";
import { TypingLoader } from "./typingLoader";
import "../styles/chat.css";

type Message = {
    role: "user" | "assistant";
    content: any;
};

/* ===== Input אחיד לרוחב ההודעות ===== */
const ChatInput = ({
    value,
    onChange,
    onSend,
    disabled = false
}: {
    value: string;
    onChange: (v: string) => void;
    onSend: () => void;
    disabled?: boolean;
}) => (
    <div className="chat-input">
        <input
            value={value}
            placeholder="Ask anything"
            onChange={e => onChange(e.target.value)}
            onKeyDown={e => e.key === "Enter" && !disabled && onSend()}
        />
        <button onClick={onSend} disabled={disabled} className="send-button">
            <img
                src="/images/appsflyer_icon.png"
                alt="Send"
                className="send-icon"
            />
        </button>
    </div>
);

export const Chat = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const isEmpty = messages.length === 0;

    // גלילה אוטומטית לתחתית כשמגיעה הודעה חדשה
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading]);

    const resetChat = () => {
        setMessages([]);
        setInput("");
        setIsLoading(false);
    };

    async function sendMessage() {
        if (isLoading) return;      // ⬅️ זה העיקר
        if (!input.trim()) return;

        const userMsg: Message = { role: "user", content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setIsLoading(true);

        try {
            const res = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMsg.content })
            });

            const data = await res.json();

            let content = data;
            if (typeof data === "string" && data.startsWith("__REACT_COMPONENT__")) {
                try {
                    content = JSON.parse(
                        data.substring("__REACT_COMPONENT__".length)
                    );
                } catch { }
            }

            setMessages(prev => [...prev, { role: "assistant", content }]);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="app-layout">
            {/* Sidebar */}
            <aside className="chat-sidebar">
                <button className="new-chat-btn" onClick={resetChat}>
                    + New Chat
                </button>
                <div className="sidebar-title">Chats</div>
                <ul className="chat-history">
                    <li className="active">Clicks by media source</li>
                    <li>Anomaly detection</li>
                    <li>Total events by app id</li>
                    <li>Growth Metrics</li>
                    <li>Acquisition Overview</li>
                    <li>Fraud Signals Overview</li>
                    <li>Media Source Comparison</li>
                    <li>Top Events by Volume</li>
                    <li>Performance Snapshot</li>
                    <li>Suspicious Activity</li>
                    <li>Events Funnel</li>
                    <li>Attribution Insights</li>
                    <li>Abnormal Click Patterns</li>
                    <li>Events by App ID</li>
                    <li>Partner Click Quality</li>
                    <li>App Performance Overview</li>
                    <li>Traffic Anomalies</li>
                    <li>Site ID Breakdown</li>
                    <li>Invalid vs Valid Clicks</li>
                    <li>Events Over Time</li>
                </ul>
            </aside>

            {/* Chat */}
            <main className={`chat-container ${isEmpty ? "empty" : ""}`}>
                {/* מצב התחלתי */}
                {isEmpty && (
                    <div className="chat-center">
                        <img
                            src="/images/appsflyer_logo.png"
                            alt="AppsFlyer"
                            className="chat-logo"
                        />

                        <ChatInput
                            value={input}
                            onChange={setInput}
                            onSend={sendMessage}
                            disabled={isLoading}
                        />
                    </div>
                )}

                {/* מצב שיחה */}
                {!isEmpty && (
                    <div className="chat-wrapper">
                        <div className="chat-messages">
                            {messages.map((msg, i) => (
                                <div className={`chat-message ${msg.role}`}>
                                    {typeof msg.content === "string" ? (
                                        <div className="bubble">
                                            {msg.content}
                                        </div>
                                    ) : (
                                        <div className="assistant-full">
                                            <UIRenderer node={msg.content} />
                                        </div>
                                    )}
                                </div>
                            ))}

                            {isLoading && (
                                <div className="chat-message assistant">
                                    <div className="bubble">
                                        <TypingLoader />
                                    </div>
                                </div>
                            )}

                            {/* אלמנט נסתר לגלילה אוטומטית */}
                            <div ref={messagesEndRef} />
                        </div>

                        <div className="chat-input">
                            <input
                                value={input}
                                placeholder="Ask anything"
                                onChange={e => setInput(e.target.value)}
                                onKeyDown={e => e.key === "Enter" && !isLoading && sendMessage()}
                            />
                            <button onClick={sendMessage} disabled={isLoading} className="send-button">
                                <img
                                    src="/images/appsflyer_icon.png"
                                    alt="Send"
                                    className="send-icon"
                                />
                            </button>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};