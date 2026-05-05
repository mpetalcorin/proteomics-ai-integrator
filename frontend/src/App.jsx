import { useState } from "react";
import axios from "axios";
import {
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ScatterChart,
  Scatter,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { Brain, Upload, Activity, FileText, Dna } from "lucide-react";
import { motion } from "framer-motion";
import "./index.css";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [report, setReport] = useState("");
  const [advanced, setAdvanced] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) return;

    setFile(selectedFile);
    setAnalysis(null);
    setPrediction(null);
    setReport("");
    setAdvanced(null);
    setStatusMessage(`Selected file: ${selectedFile.name}`);
  };

  const getErrorDetail = (error) => {
    return (
      error?.response?.data?.detail ||
      error?.response?.data?.error ||
      error?.message ||
      "Unknown error"
    );
  };

  const uploadToEndpoint = async (endpoint) => {
    if (!file) {
      alert("Please upload a proteomics CSV, TSV, TXT, or XLSX file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setStatusMessage(`Running ${endpoint}...`);

    try {
      const response = await axios.post(`${API_BASE}${endpoint}`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log(`Response from ${endpoint}:`, response.data);

      if (response.data?.error) {
        alert(`Error: ${response.data.error}`);
        setStatusMessage("Request failed.");
        return;
      }

      if (endpoint === "/api/analyze") {
        setAnalysis(response.data);
        setStatusMessage("Basic analysis completed.");
      }

      if (endpoint === "/api/predict") {
        setPrediction(response.data);
        setStatusMessage("Prediction completed.");
      }

      if (endpoint === "/api/ai-report") {
        const aiText =
          response.data?.report ||
          response.data?.message ||
          JSON.stringify(response.data, null, 2);

        setReport(aiText);
        setStatusMessage("AI report generated.");
      }
    } catch (error) {
      console.error(`Error from ${endpoint}:`, error);
      const detail = getErrorDetail(error);
      alert(`Request failed: ${detail}`);
      setStatusMessage("Request failed.");
    } finally {
      setLoading(false);
    }
  };

  const runAdvancedAnalysis = async () => {
    if (!file) {
      alert("Please upload a proteomics CSV, TSV, TXT, or XLSX file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setStatusMessage("Running advanced analysis...");

    try {
      const response = await axios.post(`${API_BASE}/api/advanced`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log("Advanced response:", response.data);

      if (response.data?.error) {
        alert(`Advanced analysis failed: ${response.data.error}`);
        setStatusMessage("Advanced analysis failed.");
        return;
      }

      setAdvanced(response.data);

      if (response.data?.warning) {
        alert(response.data.warning);
        setStatusMessage("Advanced analysis needs clearer sample labels.");
        return;
      }

      setStatusMessage("Advanced analysis completed.");
    } catch (error) {
      console.error("Advanced analysis error:", error);
      const detail = getErrorDetail(error);
      alert(`Advanced analysis failed: ${detail}`);
      setStatusMessage("Advanced analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async (type) => {
    if (!file) {
      alert("Please upload a proteomics CSV, TSV, TXT, or XLSX file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const endpoint = type === "pdf" ? "/api/report/pdf" : "/api/report/word";
    const filename =
      type === "pdf"
        ? "proteomics_ai_integrator_report.pdf"
        : "proteomics_ai_integrator_report.docx";

    setLoading(true);
    setStatusMessage(`Generating ${type.toUpperCase()} report...`);

    try {
      const response = await axios.post(`${API_BASE}${endpoint}`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        responseType: "blob",
      });

      console.log(`${type.toUpperCase()} report response:`, response);

      const contentType = response.headers["content-type"] || "";

      if (contentType.includes("application/json")) {
        const text = await response.data.text();

        try {
          const parsed = JSON.parse(text);
          alert(parsed.error || parsed.warning || text);
        } catch {
          alert(text);
        }

        setStatusMessage(`${type.toUpperCase()} report failed.`);
        return;
      }

      const blob = new Blob([response.data], { type: contentType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = filename;

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);

      setStatusMessage(`${type.toUpperCase()} report downloaded.`);
    } catch (error) {
      console.error(`${type.toUpperCase()} report error:`, error);
      const detail = getErrorDetail(error);
      alert(`Report download failed: ${detail}`);
      setStatusMessage(`${type.toUpperCase()} report failed.`);
    } finally {
      setLoading(false);
    }
  };

  const topVariableData =
    analysis?.top_variable_features?.map((item) => ({
      feature:
        item.feature.length > 18
          ? item.feature.slice(0, 18) + "..."
          : item.feature,
      variance: item.variance,
    })) || [];

  const pcSummary =
    analysis?.explained_variance?.pc1 !== undefined &&
      analysis?.explained_variance?.pc2 !== undefined
      ? `${(
        (analysis.explained_variance.pc1 + analysis.explained_variance.pc2) *
        100
      ).toFixed(1)}%`
      : "N/A";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-2xl bg-slate-900 text-white">
              <Dna size={24} />
            </div>

            <div>
              <h1 className="text-xl md:text-2xl font-bold">
                Proteomics AI Integrator
              </h1>
              <p className="text-xs md:text-sm text-slate-500">
                TMT/iTRAQ analysis, ML prediction, and AI interpretation
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid md:grid-cols-2 gap-6 items-stretch"
        >
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-2xl font-bold mb-3">
              Upload proteomics table
            </h2>

            <p className="text-slate-600 mb-6">
              Upload a TMT, iTRAQ, FragPipe, MaxQuant, or processed protein
              abundance table. The first column should contain protein or gene
              identifiers. The remaining columns should contain sample abundance
              values.
            </p>

            <label className="block border-2 border-dashed border-slate-300 rounded-3xl p-8 text-center cursor-pointer hover:bg-slate-50">
              <Upload className="mx-auto mb-3 text-slate-500" size={36} />

              <input
                type="file"
                accept=".csv,.tsv,.txt,.xlsx"
                className="hidden"
                onChange={handleFileChange}
              />

              <span className="font-medium">
                {file ? file.name : "Choose CSV, TSV, TXT, or XLSX file"}
              </span>
            </label>

            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-6 gap-3 mt-6">
              <button
                type="button"
                disabled={loading}
                onClick={() => uploadToEndpoint("/api/analyze")}
                className="rounded-2xl bg-slate-900 text-white px-4 py-3 font-semibold hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Analyze
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => uploadToEndpoint("/api/predict")}
                className="rounded-2xl bg-blue-700 text-white px-4 py-3 font-semibold hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Predict
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => uploadToEndpoint("/api/ai-report")}
                className="rounded-2xl bg-emerald-700 text-white px-4 py-3 font-semibold hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                AI Report
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={runAdvancedAnalysis}
                className="rounded-2xl bg-purple-700 text-white px-4 py-3 font-semibold hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Advanced
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => downloadReport("pdf")}
                className="rounded-2xl bg-rose-700 text-white px-4 py-3 font-semibold hover:bg-rose-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                PDF
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => downloadReport("word")}
                className="rounded-2xl bg-indigo-700 text-white px-4 py-3 font-semibold hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Word
              </button>
            </div>

            {statusMessage && (
              <p className="mt-4 text-sm text-slate-500">{statusMessage}</p>
            )}

            {loading && (
              <p className="mt-2 text-sm font-medium text-slate-700">
                Running analysis...
              </p>
            )}
          </div>

          <div className="bg-slate-900 text-white rounded-3xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-4">
              <Brain />
              <h2 className="text-2xl font-bold">What this app does</h2>
            </div>

            <p className="text-slate-300 leading-relaxed">
              This app converts complex proteomics abundance tables into
              biological insight. It performs data cleaning, missing-value
              handling, log transformation, PCA, variable-feature ranking,
              ML-based sample classification, AI-style interpretation, advanced
              biomarker ranking, volcano plotting, pathway matching, and report
              generation.
            </p>

            <div className="grid grid-cols-2 gap-3 mt-6">
              <FeatureCard title="Proteomics" text="TMT/iTRAQ abundance tables" />
              <FeatureCard title="ML" text="Predict disease or treatment groups" />
              <FeatureCard title="PCA" text="Visualize sample separation" />
              <FeatureCard title="AI" text="Generate biological summaries" />
            </div>
          </div>
        </motion.section>

        {analysis && (
          <section className="mt-8 grid lg:grid-cols-3 gap-6">
            <StatCard
              icon={<Activity />}
              title="Features"
              value={analysis.n_features ?? "N/A"}
              text="Proteins, genes, peptides, or PTM sites"
            />

            <StatCard
              icon={<FileText />}
              title="Samples"
              value={analysis.n_samples ?? "N/A"}
              text="Uploaded abundance columns"
            />

            <StatCard
              icon={<Brain />}
              title="PC1 + PC2"
              value={pcSummary}
              text="Total explained variation"
            />
          </section>
        )}

        {analysis?.pca && (
          <section className="mt-8 bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-2xl font-bold mb-4">PCA sample map</h2>

            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart>
                  <CartesianGrid />
                  <XAxis dataKey="pc1" name="PC1" />
                  <YAxis dataKey="pc2" name="PC2" />
                  <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                  <Scatter name="Samples" data={analysis.pca} fill="#0f172a" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}

        {topVariableData.length > 0 && (
          <section className="mt-8 bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-2xl font-bold mb-4">
              Top variable proteins or genes
            </h2>

            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topVariableData}>
                  <CartesianGrid />
                  <XAxis
                    dataKey="feature"
                    angle={-35}
                    textAnchor="end"
                    height={100}
                  />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="variance" fill="#1d4ed8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}

        {prediction && (
          <section className="mt-8 bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-2xl font-bold mb-4">
              Machine-learning prediction
            </h2>

            {prediction.warning ? (
              <p className="text-amber-700 bg-amber-50 rounded-2xl p-4">
                {prediction.warning}
              </p>
            ) : (
              <>
                <p className="text-lg">
                  Estimated cross-validated accuracy:
                  <span className="font-bold ml-2">
                    {prediction.cross_validated_accuracy_mean !== undefined
                      ? `${(
                        prediction.cross_validated_accuracy_mean * 100
                      ).toFixed(1)}%`
                      : "N/A"}
                  </span>
                </p>

                <p className="text-slate-600 mt-2">
                  {prediction.interpretation}
                </p>

                <div className="mt-6 grid md:grid-cols-2 gap-4">
                  {prediction.top_predictive_components?.map((item) => (
                    <div
                      key={item.component}
                      className="rounded-2xl border border-slate-200 p-4"
                    >
                      <p className="font-semibold">{item.component}</p>
                      <p className="text-sm text-slate-500">
                        Importance:{" "}
                        {item.importance !== undefined
                          ? item.importance.toFixed(4)
                          : "N/A"}
                      </p>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>
        )}

        {report && (
          <section className="mt-8 bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-2xl font-bold mb-4">
              AI biological interpretation
            </h2>

            <pre className="whitespace-pre-wrap text-slate-700 leading-relaxed">
              {report}
            </pre>
          </section>
        )}

        {advanced && !advanced.warning && (
          <section className="mt-8 space-y-8">
            <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold mb-4">
                Advanced proteomics analysis
              </h2>

              <p className="text-slate-600">
                Control samples:{" "}
                <span className="font-semibold">
                  {advanced.control_samples?.join(", ") || "N/A"}
                </span>
              </p>

              <p className="text-slate-600">
                Case samples:{" "}
                <span className="font-semibold">
                  {advanced.case_samples?.join(", ") || "N/A"}
                </span>
              </p>

              <p className="text-slate-600">
                Features analysed:{" "}
                <span className="font-semibold">
                  {advanced.n_features ?? "N/A"}
                </span>
              </p>
            </div>

            {advanced.volcano_png_base64 && (
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
                <h2 className="text-2xl font-bold mb-4">Volcano plot</h2>

                <img
                  src={`data:image/png;base64,${advanced.volcano_png_base64}`}
                  alt="Volcano plot"
                  className="w-full max-w-4xl rounded-2xl border border-slate-200"
                />
              </div>
            )}

            <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold mb-4">Top biomarker ranking</h2>

              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b bg-slate-50">
                      <th className="text-left p-3">Feature</th>
                      <th className="text-left p-3">log2FC</th>
                      <th className="text-left p-3">p-value</th>
                      <th className="text-left p-3">Score</th>
                    </tr>
                  </thead>

                  <tbody>
                    {advanced.top_biomarkers?.slice(0, 25).map((item, index) => (
                      <tr key={`${item.feature}-${index}`} className="border-b">
                        <td className="p-3 font-medium">{item.feature}</td>
                        <td className="p-3">
                          {item.log2fc !== undefined
                            ? item.log2fc.toFixed(3)
                            : "N/A"}
                        </td>
                        <td className="p-3">
                          {item.p_value !== undefined
                            ? item.p_value.toExponential(2)
                            : "N/A"}
                        </td>
                        <td className="p-3">
                          {item.biomarker_score !== undefined
                            ? item.biomarker_score.toFixed(3)
                            : "N/A"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold mb-4">Pathway enrichment</h2>

              {advanced.pathway_enrichment?.length > 0 ? (
                <div className="grid md:grid-cols-2 gap-4">
                  {advanced.pathway_enrichment.map((pathway) => (
                    <div
                      key={pathway.pathway}
                      className="rounded-2xl border border-slate-200 p-4"
                    >
                      <h3 className="font-bold text-lg">{pathway.pathway}</h3>

                      <p className="text-sm text-slate-600 mt-2">
                        Matched features:{" "}
                        {pathway.matched_features?.join(", ") || "N/A"}
                      </p>

                      <p className="text-sm text-slate-500 mt-2">
                        {pathway.interpretation}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-600">
                  No pathway matches detected using the built-in pathway engine.
                </p>
              )}
            </div>

            <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold mb-4">Explainable AI</h2>

              {advanced.explainability?.warning ? (
                <p className="text-amber-700 bg-amber-50 rounded-2xl p-4">
                  {advanced.explainability.warning}
                </p>
              ) : (
                <>
                  <p className="text-slate-600 mb-4">
                    Estimated ML accuracy:{" "}
                    <span className="font-semibold">
                      {advanced.explainability?.model_accuracy_mean !== undefined
                        ? `${(
                          advanced.explainability.model_accuracy_mean * 100
                        ).toFixed(1)}%`
                        : "N/A"}
                    </span>
                  </p>

                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {advanced.explainability?.top_explainable_features
                      ?.slice(0, 15)
                      .map((item) => (
                        <div
                          key={item.feature}
                          className="rounded-2xl border border-slate-200 p-4"
                        >
                          <p className="font-semibold">{item.feature}</p>
                          <p className="text-sm text-slate-500">
                            Importance:{" "}
                            {item.importance_mean !== undefined
                              ? item.importance_mean.toFixed(4)
                              : "N/A"}
                          </p>
                        </div>
                      ))}
                  </div>
                </>
              )}
            </div>
          </section>
        )}

        {advanced?.warning && (
          <section className="mt-8 bg-amber-50 border border-amber-200 rounded-3xl p-6">
            <h2 className="text-xl font-bold text-amber-900">
              Advanced analysis needs clearer sample names
            </h2>

            <p className="text-amber-800 mt-2">{advanced.warning}</p>

            {advanced.detected_columns && (
              <p className="text-amber-800 mt-4 text-sm">
                Detected columns: {advanced.detected_columns.join(", ")}
              </p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

function FeatureCard({ title, text }) {
  return (
    <div className="rounded-2xl bg-white/10 p-4">
      <p className="font-bold">{title}</p>
      <p className="text-sm text-slate-300">{text}</p>
    </div>
  );
}

function StatCard({ icon, title, value, text }) {
  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
      <div className="flex items-center gap-3 text-slate-700 mb-3">
        {icon}
        <h3 className="font-bold">{title}</h3>
      </div>

      <p className="text-3xl font-bold">{value}</p>
      <p className="text-slate-500 mt-2">{text}</p>
    </div>
  );
}