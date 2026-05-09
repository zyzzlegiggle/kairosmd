import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

export async function POST(request) {
  const mcpUrl = process.env.MCP_URL || "http://localhost:8000";
  const transport = new SSEClientTransport(new URL(`${mcpUrl}/sse`));
  const client = new Client({ name: "dashboard", version: "1.0.0" }, {
    capabilities: {}
  });

  try {
    const { tool, arguments: args } = await request.json();
    
    // Explicitly connect and wait for initialization
    await client.connect(transport);
    
    const result = await client.callTool({ name: tool, arguments: args || {} });

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
  } finally {
    // Always attempt to close the transport to clean up SSE sessions
    try {
      await client.close();
    } catch (e) {}
  }
}
