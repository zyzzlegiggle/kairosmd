import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

let client = null;

async function getClient() {
  if (client) return client;
  const mcpUrl = process.env.MCP_URL || "http://localhost:8000";
  const transport = new SSEClientTransport(new URL(`${mcpUrl}/sse`));
  client = new Client({ name: "dashboard", version: "1.0.0" });
  await client.connect(transport);
  return client;
}

export async function POST(request) {
  try {
    const { tool, arguments: args } = await request.json();
    const mcp = await getClient();
    const result = await mcp.callTool({ name: tool, arguments: args || {} });

    // MCP returns content array with text items
    const text = result.content
      ?.filter((c) => c.type === "text")
      .map((c) => c.text)
      .join("");

    const data = JSON.parse(text || "{}");
    return Response.json(data);
  } catch (err) {
    console.error("MCP error:", err);
    return Response.json({ error: err.message }, { status: 500 });
  }
}
