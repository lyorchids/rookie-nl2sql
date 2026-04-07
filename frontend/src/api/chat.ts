const API_BASE_URL = ''

export interface StreamCallbacks {
  onNodeStart: (node: string, label: string) => void
  onNodeProgress: (node: string, label: string, show: string) => void
  onToken: (token: string) => void
  onDone: () => void
  onError: (error: Error) => void
}

export async function streamChat(
  question: string,
  callbacks: StreamCallbacks
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Response body is not readable')
    }

    const decoder = new TextDecoder()
    let buffer = ''
    let eventType = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const dataStr = line.slice(6).trim()
          if (!dataStr) continue

          try {
            const data = JSON.parse(dataStr)
            
            switch (eventType) {
              case 'node_start':
                callbacks.onNodeStart(data.node, data.label)
                break
              case 'node_progress':
                callbacks.onNodeProgress(data.node, data.label, data.show)
                break
              case 'token':
                if (data.content) {
                  callbacks.onToken(data.content)
                }
                break
              case 'done':
                callbacks.onDone()
                return
            }
          } catch (e) {
            console.warn('Failed to parse SSE data:', dataStr)
          }
        }
      }
    }
  } catch (error) {
    callbacks.onError(error instanceof Error ? error : new Error(String(error)))
  }
}
