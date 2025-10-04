import { useEffect, useState } from "react";
import { Card, Upload, Typography, Divider, List, message, Progress } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import { getMe, listDocuments, uploadFiles } from "../services/api";
import ProgressStream from "../components/ProgressStream";

const { Title } = Typography;

export default function UploadPage() {
  const [me, setMe] = useState<any>(null);
  const [docs, setDocs] = useState<any[]>([]);
  const [percent, setPercent] = useState<number>(0);

  async function refresh() {
    try {
      const m = await getMe();
      setMe(m);
      setDocs(await listDocuments());
    } catch (e: any) {
      message.error(e.message || "Failed to load");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  // Minimal upload: call our uploader in beforeUpload and cancel AntD's default
  async function doUpload(file: File) {
    try {
      setPercent(10); // optimistic start
      await uploadFiles([file]);
      setPercent(100);
      message.success("File queued for indexing");
      setTimeout(() => setPercent(0), 800);
      setTimeout(refresh, 600);
    } catch (e: any) {
      setPercent(0);
      message.error(e.message || "Upload failed");
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-16">
      <header className="flex items-center justify-between">
        <Title level={3} className="!mb-0">Uploads</Title>
        <div className="text-sm opacity-70">Signed in as: {me?.sub ?? "unknown"}</div>
      </header>

      <Card title="Upload files (≤20)" className="shadow">
        <Upload.Dragger
          multiple
          showUploadList={false}
          beforeUpload={(file) => {
            // client-side "upload" progress (visual only)
            doUpload(file as File);
            return false; // prevent AntD from auto-uploading
          }}
        >
          <p className="ant-upload-drag-icon"><UploadOutlined /></p>
          <p className="ant-upload-text">Click or drag PDF/MD/TXT here</p>
          <p className="ant-upload-hint">You’ll see indexing progress below</p>
        </Upload.Dragger>

        {percent > 0 && percent < 100 && (
          <div style={{ marginTop: 12 }}>
            <Progress percent={percent} />
          </div>
        )}

        <Divider />
        <ProgressStream /> {/* server-side indexing progress via WebSocket */}
      </Card>

      <Card title="Your Documents" className="shadow">
        <List
          dataSource={docs}
          locale={{ emptyText: "No documents yet" }}
          renderItem={(d: any) => (
            <List.Item>
              <div className="flex justify-between w-full">
                <span>{d.filename}</span>
                <span className="text-gray-500 text-sm">
                  {d.created_at ? new Date(d.created_at).toLocaleString() : ""}
                </span>
              </div>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
}
