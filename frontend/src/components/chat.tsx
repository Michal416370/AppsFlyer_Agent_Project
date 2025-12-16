import { useState, useEffect, useRef } from "react";
import { UIRenderer } from "./UIRenderer";
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
        <div className="chat-content">
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
                <div className="sidebar-title">Chats</div>
                <ul className="chat-history">
                    <li className="active">אליפסיס ומשמעותה</li>
                    <li>דוגמאות גרפים ספריות</li>
                    <li>Git add error solution</li>
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
                    <>
                        <div className="chat-messages">
                            <div className="chat-content">
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
                        </div>

                        <ChatInput
                            value={input}
                            onChange={setInput}
                            disabled={isLoading}
                            onSend={sendMessage}
                        />
                    </>
                )}
            </main>
        </div>
    );
};