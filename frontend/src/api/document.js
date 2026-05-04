const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function summarizeDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/documents/summarize`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let message = `请求失败：${response.status}`;

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        message = errorData.detail;
      }
    } catch {
      const errorText = await response.text();
      message = errorText || message;
    }

    throw new Error(message);
  }

  return await response.json();
}

export async function summarizeDocumentStream(
  file,
  onEvent,
  summaryMode = "fast",
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("summary_mode", summaryMode);

  const response = await fetch(
    `${API_BASE_URL}/api/documents/summarize/stream`,
    {
      method: "POST",
      body: formData,
    },
  );

  if (!response.ok) {
    let message = `请求失败：${response.status}`;

    try {
      const errorData = await response.json();
      if (errorData.detail) {
        message = errorData.detail;
      }
    } catch {
      const errorText = await response.text();
      message = errorText || message;
    }

    throw new Error(message);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        onEvent(JSON.parse(line));
      } catch {
        // skip malformed lines
      }
    }
  }
}

export async function askQuestion(docId, question) {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, question }),
  });

  if (!response.ok) {
    let message = `请求失败：${response.status}`;

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        message = errorData.detail;
      }
    } catch {
      const errorText = await response.text();
      message = errorText || message;
    }

    throw new Error(message);
  }

  return await response.json();
}
