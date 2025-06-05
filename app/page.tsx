"use client";

import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "¡Hola! Soy Abraham Licona, tu asistente de reservas hoteleras. Describe tu reservación y te ayudo a convertirla en formato para el modelo.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
    setMessages((msgs) => [
      ...msgs,
      {
        role: "assistant",
        content: "Operación cancelada. ¿En qué más puedo ayudarte?",
      },
    ]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setError("");
    setLoading(true);
    const userMsg = { role: "user", content: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    // Resetear altura de la textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "45px";
    }

    // Crear un nuevo AbortController para esta solicitud
    abortControllerRef.current = new AbortController();

    try {
      const res = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userMessage: input }),
        signal: abortControllerRef.current.signal,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Error al procesar el mensaje");
      }

      // Manejar la respuesta según su estructura
      let responseContent = "";
      if (data.prediction && typeof data.prediction === "object") {
        if (data.prediction.status === "error") {
          throw new Error(data.prediction.message);
        }
        responseContent = data.prediction.message || "";
        if (data.prediction.explanation) {
          responseContent += "\n\n" + data.prediction.explanation;
        }
      } else if (typeof data.prediction === "string") {
        responseContent = data.prediction;
      } else {
        responseContent = "Respuesta no válida del servidor";
      }

      // Limpiar la respuesta de caracteres especiales
      responseContent = responseContent
        .replace(/[{}]/g, "")
        .replace(/^"|"$/g, "")
        .replace(/\\n/g, "\n")
        .replace(/\\u00f3/g, "ó")
        .replace(/\\u00e1/g, "á")
        .replace(/\\u00e9/g, "é")
        .replace(/\\u00ed/g, "í")
        .replace(/\\u00fa/g, "ú")
        .replace(/\n\s*\n/g, "\n\n")
        .trim();

      setMessages((msgs) => [
        ...msgs,
        { role: "assistant", content: responseContent },
      ]);
    } catch (err: any) {
      if (err.name === "AbortError") {
        console.log("Solicitud cancelada");
        return;
      }
      setError(err.message);
      setMessages((msgs) => [
        ...msgs,
        { role: "assistant", content: "Ocurrió un error: " + err.message },
      ]);
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      <header className="py-6 px-4 bg-red-700 shadow-md sticky top-0 z-10">
        <h1 className="text-3xl font-bold text-white text-center tracking-tight">
          Procesador de Reservaciones
        </h1>
        <p className="text-center text-white mt-2">
          Este recurso es propiedad exclusiva del Equipo 5.
        </p>
      </header>
      <main className="flex-1 overflow-y-auto px-2 md:px-0">
        <div className="max-w-2xl mx-auto py-6 flex flex-col gap-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <img
                  src="/prueba.png"
                  alt="Foto del modelo"
                  className="w-[27px] h-[27px] rounded-full mr-3 self-end"
                  style={{ objectFit: "cover" }}
                />
              )}
              <div
                className={`rounded-2xl px-4 py-3 max-w-[80%] shadow-md text-base whitespace-pre-wrap
                  ${
                    msg.role === "user"
                      ? "bg-red-700 text-white rounded-br-none"
                      : "bg-white text-gray-800 rounded-bl-none"
                  }
                `}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="px-4 py-3 rounded-lg bg-white text-black rounded-tl-none max-w-[60ch] shadow-md">
                <div className="flex space-x-1">
                  <div
                    className="w-2 h-2 bg-black rounded-full animate-pulse"
                    style={{ animationDelay: "0ms" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-black rounded-full animate-pulse"
                    style={{ animationDelay: "300ms" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-black rounded-full animate-pulse"
                    style={{ animationDelay: "600ms" }}
                  ></div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
      </main>
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-2xl mx-auto flex flex-col items-end gap-2 px-2 pb-6 sticky bottom-0 bg-gradient-to-t from-white via-white/80 to-transparent"
        style={{ backdropFilter: "blur(6px)" }}
      >
        <div className="w-full flex items-end gap-2 ">
          <textarea
            ref={textareaRef}
            className="flex-1 rounded-[30px] border border-red-600 px-5 py-3 outline-none bg-white resize-none caret-red-600"
            placeholder="Describe tu reservación..."
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              // Auto-resize the textarea
              e.target.style.height = "auto";
              e.target.style.height =
                Math.min(e.target.scrollHeight, 300) + "px";
            }}
            disabled={loading}
            style={{ maxHeight: "150px", minHeight: "45px", height: "45px" }}
            rows={1}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          {loading ? (
            <button
              type="button"
              onClick={handleCancel}
              className="bg-red-600 transition-color ease-in-out duration-500 cursor-pointer hover:bg-red-700 h-[40px] w-[40px] text-white font-semibold flex items-center justify-center rounded-full shadow transition disabled:bg-gray-300"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width={24}
                height={24}
                fill="none"
                className="icon-lg"
              >
                <rect
                  width={10}
                  height={10}
                  x={7}
                  y={7}
                  fill="currentColor"
                  rx={1.25}
                />
              </svg>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="bg-red-600 transition-color ease-in-out duration-500 cursor-pointer hover:bg-red-700 h-[40px] w-[40px] text-white font-semibold flex items-center justify-center rounded-full shadow transition disabled:bg-gray-300"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width={18}
                height={18}
                fill="none"
                className="icon-md"
              >
                <path
                  fill="currentColor"
                  d="M8 15V5.412L4.707 8.706a1 1 0 1 1-1.414-1.414l5-5 .076-.068a1 1 0 0 1 1.338.068l5 5 .068.076a1 1 0 0 1-1.406 1.407l-.076-.069L10 5.413V15a1 1 0 1 1-2 0Z"
                />
              </svg>
            </button>
          )}
        </div>
      </form>
      {error && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 bg-red-100 text-red-700 px-6 py-3 rounded-xl shadow-lg z-50">
          {error}
        </div>
      )}
    </div>
  );
}
