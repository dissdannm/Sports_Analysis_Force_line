// windows_client/src/pages/Dashboard.tsx

import React, { useEffect, useMemo, useState } from "react"
import type {
  AnalyzeFrameRequest,
  AnalyzeFrameResponse,
  MotionDetailResponse,
  MotionItem,
  MotionListResponse,
} from "../types/api"

const defaultApiBase = "http://127.0.0.1:8000"

function createMockAnalyzeRequest(motionId: string): AnalyzeFrameRequest {
  return {
    motion_id: motionId,
    session_id: "windows_client_session_001",
    timestamp_ms: Date.now(),
    landmarks: {
      nose: { x: 0.52, y: 0.15, z: 0.01, visibility: 0.98 },
      left_shoulder: { x: 0.44, y: 0.28, z: 0.02, visibility: 0.97 },
      right_shoulder: { x: 0.58, y: 0.28, z: 0.02, visibility: 0.97 },
      left_elbow: { x: 0.40, y: 0.40, z: 0.03, visibility: 0.95 },
      right_elbow: { x: 0.62, y: 0.40, z: 0.03, visibility: 0.95 },
      left_wrist: { x: 0.36, y: 0.52, z: 0.03, visibility: 0.95 },
      right_wrist: { x: 0.66, y: 0.52, z: 0.03, visibility: 0.95 },
      left_hip: { x: 0.46, y: 0.52, z: 0.02, visibility: 0.96 },
      right_hip: { x: 0.56, y: 0.52, z: 0.02, visibility: 0.96 },
      left_knee: { x: 0.47, y: 0.72, z: 0.02, visibility: 0.96 },
      right_knee: { x: 0.57, y: 0.72, z: 0.02, visibility: 0.96 },
      left_ankle: { x: 0.48, y: 0.90, z: 0.02, visibility: 0.96 },
      right_ankle: { x: 0.58, y: 0.90, z: 0.02, visibility: 0.96 },
    },
  }
}

export default function Dashboard() {
  const [apiBaseUrl, setApiBaseUrl] = useState(defaultApiBase)
  const [motions, setMotions] = useState<MotionItem[]>([])
  const [currentMotionId, setCurrentMotionId] = useState("")
  const [currentMotionDetail, setCurrentMotionDetail] = useState<MotionDetailResponse | null>(null)

  const [healthStatus, setHealthStatus] = useState<"idle" | "ok" | "error">("idle")
  const [loadingMotions, setLoadingMotions] = useState(false)
  const [loadingMotionDetail, setLoadingMotionDetail] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)

  const [analysisResult, setAnalysisResult] = useState<AnalyzeFrameResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState("")

  const currentMotionName = useMemo(() => {
    return motions.find((item) => item.motion_id === currentMotionId)?.motion_name ?? ""
  }, [motions, currentMotionId])

  useEffect(() => {
    void checkHealth()
    void loadMotions()
  }, [])

  useEffect(() => {
    if (!currentMotionId) return
    void loadMotionDetail(currentMotionId)
  }, [currentMotionId])

  async function checkHealth() {
    setErrorMessage("")
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/health`)
      if (!response.ok) {
        throw new Error(`健康检查失败: ${response.status}`)
      }
      setHealthStatus("ok")
    } catch (error) {
      console.error(error)
      setHealthStatus("error")
      setErrorMessage("无法连接后端服务，请检查后端是否启动。")
    }
  }

  async function loadMotions() {
    setLoadingMotions(true)
    setErrorMessage("")
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/motions`)
      if (!response.ok) {
        throw new Error(`获取动作列表失败: ${response.status}`)
      }

      const data: MotionListResponse = await response.json()
      setMotions(data.items)

      if (data.items.length > 0) {
        setCurrentMotionId((prev) => prev || data.items[0].motion_id)
      }
    } catch (error) {
      console.error(error)
      setErrorMessage("加载动作列表失败。")
    } finally {
      setLoadingMotions(false)
    }
  }

  async function loadMotionDetail(motionId: string) {
    setLoadingMotionDetail(true)
    setErrorMessage("")
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/motions/${motionId}`)
      if (!response.ok) {
        throw new Error(`获取动作详情失败: ${response.status}`)
      }

      const data: MotionDetailResponse = await response.json()
      setCurrentMotionDetail(data)
    } catch (error) {
      console.error(error)
      setErrorMessage(`加载动作详情失败：${motionId}`)
      setCurrentMotionDetail(null)
    } finally {
      setLoadingMotionDetail(false)
    }
  }

  async function handleAnalyzeTestFrame() {
    if (!currentMotionId) {
      setErrorMessage("请先选择动作。")
      return
    }

    setAnalyzing(true)
    setErrorMessage("")

    try {
      const requestBody = createMockAnalyzeRequest(currentMotionId)

      const response = await fetch(`${apiBaseUrl}/api/v1/analyze/frame`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error(`单帧分析失败: ${response.status}`)
      }

      const data: AnalyzeFrameResponse = await response.json()
      setAnalysisResult(data)
    } catch (error) {
      console.error(error)
      setErrorMessage("调用单帧分析接口失败。")
    } finally {
      setAnalyzing(false)
    }
  }

  function renderHealthBadge() {
    if (healthStatus === "ok") {
      return <span style={styles.badgeSuccess}>Backend Online</span>
    }

    if (healthStatus === "error") {
      return <span style={styles.badgeDanger}>Backend Offline</span>
    }

    return <span style={styles.badgeNeutral}>Backend Unknown</span>
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <header style={styles.header}>
          <div>
            <h1 style={styles.title}>Windows 运动力线分析前端</h1>
            <p style={styles.subtitle}>
              企业第一版 Windows 客户端控制台。当前用于动作选择、后端联调、指标展示和告警验证。
            </p>
          </div>
          <div>{renderHealthBadge()}</div>
        </header>

        <section style={styles.grid}>
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>连接与动作选择</h2>

            <label style={styles.label}>后端地址</label>
            <input
              style={styles.input}
              value={apiBaseUrl}
              onChange={(e) => setApiBaseUrl(e.target.value)}
              placeholder="http://127.0.0.1:8000"
            />

            <div style={styles.buttonRow}>
              <button style={styles.secondaryButton} onClick={() => void checkHealth()}>
                检查后端连接
              </button>
              <button style={styles.secondaryButton} onClick={() => void loadMotions()}>
                刷新动作列表
              </button>
            </div>

            <label style={styles.label}>当前动作</label>
            <select
              style={styles.select}
              value={currentMotionId}
              onChange={(e) => setCurrentMotionId(e.target.value)}
              disabled={loadingMotions || motions.length === 0}
            >
              {motions.length === 0 ? (
                <option value="">暂无动作</option>
              ) : (
                motions.map((motion) => (
                  <option key={motion.motion_id} value={motion.motion_id}>
                    {motion.motion_name} ({motion.motion_id})
                  </option>
                ))
              )}
            </select>

            <div style={styles.tipBox}>
              <div style={styles.tipTitle}>动作选择规范</div>
              <div style={styles.tipText}>
                前端按钮点击后只传 <code>motion_id</code>，不要把中文名当主键。
              </div>
            </div>
          </div>

          <div style={styles.card}>
            <h2 style={styles.cardTitle}>动作详情</h2>

            {loadingMotionDetail ? (
              <div style={styles.placeholder}>正在加载动作详情...</div>
            ) : !currentMotionDetail ? (
              <div style={styles.placeholder}>当前没有动作详情。</div>
            ) : (
              <div style={styles.detailBlock}>
                <div style={styles.detailRow}>
                  <span style={styles.detailKey}>动作名称</span>
                  <span style={styles.detailValue}>{currentMotionDetail.motion_name}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailKey}>动作 ID</span>
                  <span style={styles.detailValue}>{currentMotionDetail.motion_id}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailKey}>版本</span>
                  <span style={styles.detailValue}>{currentMotionDetail.version}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailKey}>描述</span>
                  <span style={styles.detailValue}>{currentMotionDetail.description}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailKey}>稳定帧数</span>
                  <span style={styles.detailValue}>{currentMotionDetail.stable_frames}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailKey}>语音冷却</span>
                  <span style={styles.detailValue}>{currentMotionDetail.voice_cooldown_ms} ms</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailKey}>最小保持</span>
                  <span style={styles.detailValue}>{currentMotionDetail.min_hold_ms} ms</span>
                </div>

                <div style={{ marginTop: 16 }}>
                  <div style={styles.subTitle}>启用指标</div>
                  <div style={styles.tagWrap}>
                    {currentMotionDetail.enabled_metrics.map((metric) => (
                      <span key={metric} style={styles.tag}>
                        {metric}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        <section style={styles.card}>
          <h2 style={styles.cardTitle}>单帧分析联调</h2>
          <p style={styles.subtitleSmall}>
            当前使用 mock landmarks 直接调用 <code>/api/v1/analyze/frame</code>，用于验证前后端接口契约。
          </p>

          <div style={styles.buttonRow}>
            <button style={styles.primaryButton} onClick={() => void handleAnalyzeTestFrame()} disabled={analyzing}>
              {analyzing ? "分析中..." : `测试分析当前动作${currentMotionName ? `：${currentMotionName}` : ""}`}
            </button>
          </div>

          {errorMessage && <div style={styles.errorBox}>{errorMessage}</div>}
        </section>

        <section style={styles.grid}>
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>指标结果</h2>

            {!analysisResult ? (
              <div style={styles.placeholder}>尚未拿到分析结果。</div>
            ) : !analysisResult.pose_detected ? (
              <div style={styles.placeholder}>当前未检测到有效姿态。</div>
            ) : (
              <div style={styles.metricGrid}>
                {Object.entries(analysisResult.metrics).map(([key, value]) => (
                  <div key={key} style={styles.metricCard}>
                    <div style={styles.metricKey}>{key}</div>
                    <div style={styles.metricValue}>{value.toFixed(4)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={styles.card}>
            <h2 style={styles.cardTitle}>告警结果</h2>

            {!analysisResult ? (
              <div style={styles.placeholder}>尚未拿到告警结果。</div>
            ) : analysisResult.alerts.length === 0 ? (
              <div style={styles.placeholder}>当前没有告警。</div>
            ) : (
              <div style={styles.alertList}>
                {analysisResult.alerts.map((alert, index) => (
                  <div
                    key={`${alert.code}-${index}`}
                    style={{
                      ...styles.alertItem,
                      ...(alert.level === "severe"
                        ? styles.alertSevere
                        : alert.level === "moderate"
                        ? styles.alertModerate
                        : styles.alertMild),
                    }}
                  >
                    <div style={styles.alertTopRow}>
                      <strong>{alert.metric_id}</strong>
                      <span>{alert.level}</span>
                    </div>
                    <div style={{ marginTop: 8 }}>{alert.message}</div>
                    <div style={styles.alertSubText}>speak: {String(alert.speak)}</div>
                    <div style={styles.alertSubText}>speak_text: {alert.speak_text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <section style={styles.card}>
          <h2 style={styles.cardTitle}>前端开发约定</h2>
          <ul style={styles.list}>
            <li>按钮点击后，前端统一保存并传递 <code>motion_id</code>。</li>
            <li>前端不要自己发明指标名和告警字段名，全部以后端返回为准。</li>
            <li>前端显示用 <code>alert.message</code>，本地播报优先用 <code>alert.speak_text</code>。</li>
            <li>后续接真实摄像头和 landmarks 时，沿用当前 <code>AnalyzeFrameRequest</code> 结构。</li>
          </ul>
        </section>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    background: "#f3f4f6",
    padding: 24,
    fontFamily: "Segoe UI, Arial, sans-serif",
  },
  container: {
    maxWidth: 1440,
    margin: "0 auto",
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 16,
    background: "#ffffff",
    borderRadius: 20,
    padding: 24,
    boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
  },
  title: {
    margin: 0,
    fontSize: 30,
    fontWeight: 700,
    color: "#0f172a",
  },
  subtitle: {
    margin: "8px 0 0 0",
    fontSize: 14,
    lineHeight: 1.7,
    color: "#64748b",
  },
  subtitleSmall: {
    margin: "6px 0 0 0",
    fontSize: 13,
    lineHeight: 1.7,
    color: "#64748b",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 20,
  },
  card: {
    background: "#ffffff",
    borderRadius: 20,
    padding: 20,
    boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
  },
  cardTitle: {
    margin: 0,
    fontSize: 20,
    fontWeight: 700,
    color: "#111827",
  },
  label: {
    display: "block",
    marginTop: 16,
    marginBottom: 8,
    fontSize: 14,
    fontWeight: 600,
    color: "#334155",
  },
  input: {
    width: "100%",
    boxSizing: "border-box",
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid #cbd5e1",
    fontSize: 14,
    outline: "none",
  },
  select: {
    width: "100%",
    boxSizing: "border-box",
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid #cbd5e1",
    fontSize: 14,
    outline: "none",
    background: "#ffffff",
  },
  buttonRow: {
    display: "flex",
    gap: 12,
    flexWrap: "wrap",
    marginTop: 16,
  },
  primaryButton: {
    background: "#2563eb",
    color: "#ffffff",
    border: "none",
    borderRadius: 12,
    padding: "12px 18px",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  secondaryButton: {
    background: "#ffffff",
    color: "#0f172a",
    border: "1px solid #cbd5e1",
    borderRadius: 12,
    padding: "12px 18px",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  badgeSuccess: {
    display: "inline-block",
    padding: "8px 12px",
    borderRadius: 999,
    background: "#dcfce7",
    color: "#166534",
    fontSize: 13,
    fontWeight: 700,
  },
  badgeDanger: {
    display: "inline-block",
    padding: "8px 12px",
    borderRadius: 999,
    background: "#fee2e2",
    color: "#991b1b",
    fontSize: 13,
    fontWeight: 700,
  },
  badgeNeutral: {
    display: "inline-block",
    padding: "8px 12px",
    borderRadius: 999,
    background: "#e5e7eb",
    color: "#374151",
    fontSize: 13,
    fontWeight: 700,
  },
  detailBlock: {
    marginTop: 12,
  },
  detailRow: {
    display: "flex",
    justifyContent: "space-between",
    gap: 12,
    padding: "8px 0",
    borderBottom: "1px solid #e5e7eb",
  },
  detailKey: {
    color: "#64748b",
    fontSize: 14,
    minWidth: 110,
  },
  detailValue: {
    color: "#0f172a",
    fontSize: 14,
    textAlign: "right",
    flex: 1,
  },
  subTitle: {
    fontSize: 14,
    fontWeight: 700,
    color: "#334155",
    marginBottom: 8,
  },
  tagWrap: {
    display: "flex",
    gap: 8,
    flexWrap: "wrap",
  },
  tag: {
    display: "inline-block",
    padding: "6px 10px",
    borderRadius: 999,
    background: "#e2e8f0",
    color: "#1e293b",
    fontSize: 12,
    fontWeight: 600,
  },
  tipBox: {
    marginTop: 16,
    padding: 14,
    borderRadius: 14,
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
  },
  tipTitle: {
    fontSize: 14,
    fontWeight: 700,
    color: "#334155",
  },
  tipText: {
    marginTop: 6,
    fontSize: 13,
    lineHeight: 1.6,
    color: "#64748b",
  },
  placeholder: {
    marginTop: 16,
    padding: 16,
    borderRadius: 14,
    background: "#f8fafc",
    border: "1px dashed #cbd5e1",
    fontSize: 14,
    color: "#64748b",
  },
  metricGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
    gap: 12,
    marginTop: 16,
  },
  metricCard: {
    border: "1px solid #e5e7eb",
    borderRadius: 16,
    padding: 14,
    background: "#ffffff",
  },
  metricKey: {
    fontSize: 13,
    color: "#64748b",
  },
  metricValue: {
    marginTop: 8,
    fontSize: 24,
    fontWeight: 700,
    color: "#0f172a",
  },
  alertList: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
    marginTop: 16,
  },
  alertItem: {
    borderRadius: 16,
    padding: 14,
    border: "1px solid transparent",
  },
  alertMild: {
    background: "#fef9c3",
    color: "#854d0e",
    borderColor: "#fde68a",
  },
  alertModerate: {
    background: "#ffedd5",
    color: "#9a3412",
    borderColor: "#fdba74",
  },
  alertSevere: {
    background: "#fee2e2",
    color: "#991b1b",
    borderColor: "#fca5a5",
  },
  alertTopRow: {
    display: "flex",
    justifyContent: "space-between",
    gap: 12,
    fontSize: 14,
  },
  alertSubText: {
    marginTop: 6,
    fontSize: 12,
    opacity: 0.85,
  },
  errorBox: {
    marginTop: 16,
    padding: 12,
    borderRadius: 12,
    background: "#fee2e2",
    color: "#991b1b",
    fontSize: 14,
    border: "1px solid #fca5a5",
  },
  list: {
    marginTop: 12,
    paddingLeft: 20,
    color: "#475569",
    lineHeight: 1.8,
    fontSize: 14,
  },
}