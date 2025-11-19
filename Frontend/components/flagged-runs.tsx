import React, { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
interface Message {
  id: number;
  text: string;
  sender: "user" | "agent";
  name?: string;
  timestamp: string;
}

interface FlaggedRun {
  reason: string;
  messages: Message[];
}

export const InspectionWindow: React.FC = () => {
  const [flaggedRuns, setFlaggedRuns] = useState<FlaggedRun[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [openRunIndex, setOpenRunIndex] = useState<number | null>(null);

  // Fetch flagged runs on mount
  useEffect(() => {
    setLoading(true);
    fetch("http://localhost:8001/flagged-runs")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Server responded with ${res.status}`);
        }
        return res.json();
      })
      .then((data: FlaggedRun[]) => {
        setFlaggedRuns(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching flagged runs:", err);
        setError("Could not load flagged runs.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div>Loading flagged runs…</div>;
  }

  if (error) {
    return <div style={{ color: "red" }}>{error}</div>;
  }

  if (flaggedRuns.length === 0) {
    return <div>No flagged runs found.</div>;
  }

  return (
    <div style={{ padding: "1rem" }}>
      <h1>Flagged Runs</h1>

      {/* List each flagged run with an "Inspect Run" button */}
      {flaggedRuns.map((run, index) => (
        <div
          key={index}
          style={{
            border: "1px solid #ccc",
            borderRadius: "4px",
            marginBottom: "1rem",
            padding: "0.5rem",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <h2 style={{ margin: 0, fontSize: "1.1rem" }}>
              Run #{index + 1}
            </h2>
            <button
              onClick={() => setOpenRunIndex(index)}
              style={{
                backgroundColor: "#007bff",
                color: "#fff",
                border: "none",
                borderRadius: "3px",
                padding: "0.3rem 0.6rem",
                cursor: "pointer",
              }}
            >
              Inspect Run
            </button>
          </div>
          <div style={{ marginTop: "0.5rem", color: "#555" }}>
            Feedback: <em>{run.reason}</em>
          </div>
        </div>
      ))}

      {/* Modal for inspecting a single run */}
      {openRunIndex !== null && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: "#fff",
              borderRadius: "6px",
              width: "80%",
              maxHeight: "80%",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "0.75rem 1rem",
                borderBottom: "1px solid #ddd",
                backgroundColor: "#f5f5f5",
              }}
            >
              <h2 style={{ margin: 0, fontSize: "1.25rem" }}>
                Inspect Run #{openRunIndex + 1}
              </h2>
              <button
                onClick={() => setOpenRunIndex(null)}
                style={{
                  background: "transparent",
                  border: "none",
                  fontSize: "1.25rem",
                  cursor: "pointer",
                  lineHeight: 1,
                }}
              >
                ×
              </button>
            </div>

            {/* Modal Body: messages on the left, reasoning on the right */}
            <div
              style={{
                display: "flex",
                flex: 1,
                overflow: "hidden",
              }}
            >
              {/* Messages Column */}
              <div
                style={{
                  flex: 1,
                  padding: "1rem",
                  overflowY: "auto",
                  borderRight: "1px solid #eee",
                }}
              >
                {flaggedRuns[openRunIndex].messages.map((msg) => (
                  <div
                    key={msg.id}
                    style={{
                      marginBottom: "1rem",
                      padding: "0.75rem",
                      backgroundColor:
                        msg.sender === "user" ? "#e6f7ff" : "#fffbe6",
                      borderRadius: "4px",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "0.9rem",
                        fontWeight: 500,
                        marginBottom: "0.25rem",
                      }}
                    >
                      {msg.sender === "user" ? "You" : msg.name || "Agent"}{" "}
                      <span style={{ fontSize: "0.8rem", color: "#666" }}>
                        ({msg.timestamp})
                      </span>
                    </div>
                    <div
                      style={{
                        fontSize: "0.95rem",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                     <ReactMarkdown
                                               remarkPlugins={[remarkGfm]}
                                               components={{
                                                 table: ({ node, ...props }) => (
                                                   <div className="overflow-x-auto mb-4 mt-4">
                                                     <table
                                                       className="border-collapse border border-gray-300 min-w-full"
                                                       style={{ color: "black" }}
                                                       {...props}
                                                     />
                                                   </div>
                                                 ),
                                                 thead: ({ node, ...props }) => <thead className="bg-gray-100" {...props} />,
                                                 th: ({ node, ...props }) => (
                                                   <th className="border border-gray-300 px-3 py-1 text-left" {...props} />
                                                 ),
                                                 td: ({ node, ...props }) => (
                                                   <td className="border border-gray-300 px-3 py-1 hover:bg-gray-50" {...props} />
                                                 ),
                                                 tr: ({ node, ...props }) => <tr className="odd:bg-white even:bg-gray-50" {...props} />,
                                                 hr: ({ node, ...props }) => <hr style={{ marginBottom: "1em", marginTop: "1em" }} />,
                                                 li: ({ node, ...props }) => <li className="mb-1 ml-4 list-disc" {...props}/>,
                                                 ul: ({ node, ...props }) => <ul  {...props} style={{marginBottom: "2em"}}/>,
                                               }}
                                             >
                                               {msg.text}
                                             </ReactMarkdown>
                    </div>
                  </div>
                ))}
              </div>

              {/* Reasoning Column */}
              <div
                style={{
                  width: "30%",
                  padding: "1rem",
                  overflowY: "auto",
                  backgroundColor: "#fafafa",
                }}
              >
                <h3 style={{ marginTop: 0, fontSize: "1.1rem" }}>
                  Feedback
                </h3>
                <div
                  style={{
                    fontSize: "0.95rem",
                    lineHeight: 1.4,
                    color: "#333",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {flaggedRuns[openRunIndex].reason}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InspectionWindow;
