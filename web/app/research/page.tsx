// const trainingHistory = [
//   { epoch: 1, trainF1: 43.50, valF1: 51.50 },
//   { epoch: 2, trainF1: 71.51, valF1: 54.38 },
//   { epoch: 3, trainF1: 73.89, valF1: 62.14 },
//   { epoch: 4, trainF1: 82.44, valF1: 61.97 },
//   { epoch: 5, trainF1: 85.98, valF1: 65.69 },
//   { epoch: 6, trainF1: 89.77, valF1: 66.31 },
//   { epoch: 7, trainF1: 92.43, valF1: 65.24 },
//   { epoch: 8, trainF1: 95.03, valF1: 64.86 },
//   { epoch: 9, trainF1: 95.14, valF1: 64.31 },
//   { epoch: 10, trainF1: 94.47, valF1: 64.63 },
//   { epoch: 11, trainF1: 97.21, valF1: 64.46 }
// ];
// const modelComparison = [
//   {
//     name: "EfficientNet-B0",
//     accuracy: 75.96,
//     precision: 75.08,
//     recall: 74.47,
//     f1: 74.58,
//     inference: 18.95,
//     selected: true
//   },
//   {
//     name: "ResNet18",
//     accuracy: 74.04,
//     precision: 73.25,
//     recall: 72.89,
//     f1: 72.72,
//     inference: 17.04,
//     selected: false
//   },
//   {
//     name: "MobileNetV3-Small",
//     accuracy: 72.12,
//     precision: 71.29,
//     recall: 70.45,
//     f1: 70.35,
//     inference: 2.88,
//     selected: false
//   }
// ];
// const datasetMetrics = {
//   train: 508,
//   validation: 117,
//   test: 104,
//   total: 729,
//   bestValidationF1: 66.31,
//   inferenceMs: 18.95,
//   epochsRun: 11,
//   bestEpoch: 6
// };

// const modelMetrics = {
//   name: "EfficientNet-B0",
//   version: "wound-type-v1",
//   accuracy: 75.96,
//   precision: 75.08,
//   recall: 74.47,
//   f1: 74.58,
//   testImages: 104
// };

// const classMetrics = [
//   { name: "Diabetic", f1: 74.07 },
//   { name: "Pressure", f1: 63.41 },
//   { name: "Surgical", f1: 75.56 },
//   { name: "Venous", f1: 85.29 }
// ];

// const confusionMatrix = {
//   labels: ["Diabetic", "Pressure", "Surgical", "Venous"],
//   values: [
//     [20, 4, 1, 3],
//     [4, 13, 1, 2],
//     [2, 3, 17, 2],
//     [0, 1, 2, 29]
//   ]
// };
// function TrainingHistoryChart() {
//   const width = 900;
//   const height = 320;
//   const padding = 50;

//   const maxEpoch = Math.max(...trainingHistory.map((d) => d.epoch));
//   const minF1 = 40;
//   const maxF1 = 100;

//   const xScale = (epoch: number) =>
//     padding +
//     ((epoch - 1) / (maxEpoch - 1)) *
//       (width - padding * 2);

//   const yScale = (value: number) =>
//     height -
//     padding -
//     ((value - minF1) / (maxF1 - minF1)) *
//       (height - padding * 2);

//   const trainPoints = trainingHistory
//     .map((d) => `${xScale(d.epoch)},${yScale(d.trainF1)}`)
//     .join(" ");

//   const valPoints = trainingHistory
//     .map((d) => `${xScale(d.epoch)},${yScale(d.valF1)}`)
//     .join(" ");

//   return (
//     <div style={{ overflowX: "auto", marginTop: 18 }}>
//       <svg
//         viewBox={`0 0 ${width} ${height}`}
//         style={{ width: "100%", minWidth: 700 }}
//       >
//         {/* Y-axis labels */}
//         {[40, 50, 60, 70, 80, 90, 100].map((value) => (
//           <g key={value}>
//             <line
//               x1={padding}
//               x2={width - padding}
//               y1={yScale(value)}
//               y2={yScale(value)}
//               stroke="#e5e7eb"
//             />
//             <text
//               x={10}
//               y={yScale(value) + 4}
//               fontSize="12"
//               fill="#6b7280"
//             >
//               {value}%
//             </text>
//           </g>
//         ))}

//         {/* X-axis labels */}
//         {trainingHistory.map((d) => (
//           <text
//             key={d.epoch}
//             x={xScale(d.epoch)}
//             y={height - 15}
//             textAnchor="middle"
//             fontSize="12"
//             fill="#6b7280"
//           >
//             {d.epoch}
//           </text>
//         ))}

//         {/* Train line */}
//         <polyline
//           fill="none"
//           stroke="currentColor"
//           strokeWidth="3"
//           points={trainPoints}
//         />

//         {/* Validation line */}
//         <polyline
//           fill="none"
//           stroke="#7c3aed"
//           strokeWidth="3"
//           points={valPoints}
//         />

//         {/* Best epoch marker */}
//         <line
//           x1={xScale(datasetMetrics.bestEpoch)}
//           x2={xScale(datasetMetrics.bestEpoch)}
//           y1={padding}
//           y2={height - padding}
//           stroke="#ef4444"
//           strokeDasharray="5 5"
//         />

//         <text
//           x={xScale(datasetMetrics.bestEpoch) + 8}
//           y={padding + 14}
//           fontSize="12"
//           fill="#ef4444"
//         >
//           Best epoch {datasetMetrics.bestEpoch}
//         </text>
//       </svg>

//       <div
//         style={{
//           display: "flex",
//           gap: 18,
//           marginTop: 10,
//           flexWrap: "wrap"
//         }}
//       >
//         <span className="small muted">
//           Train Macro F1
//         </span>

//         <span className="small muted">
//           Validation Macro F1
//         </span>

//         <span className="small muted">
//           Best validation epoch
//         </span>
//       </div>
//     </div>
//   );
// }
// export default function ResearchPage() {
//   return (
//     <>
//       {/* HEADER */}
//       <section className="card">
//         <p className="small history-eyebrow">
//           RESEARCH DASHBOARD
//         </p>

//         <h1>Wound Type Model Evaluation</h1>

//         <p className="muted">
//           Evaluation results for the trained multi-class wound
//           classification model using the held-out test dataset.
//         </p>

//         <div
//           style={{
//             marginTop: 18,
//             display: "flex",
//             gap: 12,
//             flexWrap: "wrap"
//           }}
//         >
//           <span className="status confident">
//             EfficientNet-B0
//           </span>

//           <span className="status confident">
//             wound-type-v1
//           </span>

//           <span className="status confident">
//             Research
//           </span>
//         </div>
//       </section>

//       {/* MAIN METRICS */}
//       <section
//         className="history-stats"
//         style={{ marginTop: 18 }}
//       >
//         <article className="card">
//           <p className="small muted">
//             ACCURACY
//           </p>

//           <div className="kpi">
//             {modelMetrics.accuracy.toFixed(2)}%
//           </div>

//           <p className="muted">
//             Overall correctly classified test images.
//           </p>
//         </article>

//         <article className="card">
//           <p className="small muted">
//             MACRO PRECISION
//           </p>

//           <div className="kpi">
//             {modelMetrics.precision.toFixed(2)}%
//           </div>

//           <p className="muted">
//             Average precision across all wound classes.
//           </p>
//         </article>

//         <article className="card">
//           <p className="small muted">
//             MACRO RECALL
//           </p>

//           <div className="kpi">
//             {modelMetrics.recall.toFixed(2)}%
//           </div>

//           <p className="muted">
//             Average recall across all wound classes.
//           </p>
//         </article>

//         <article className="card">
//           <p className="small muted">
//             MACRO F1
//           </p>

//           <div className="kpi">
//             {modelMetrics.f1.toFixed(2)}%
//           </div>

//           <p className="muted">
//             Primary balanced performance metric.
//           </p>
//         </article>
//       </section>

//       {/* MODEL INFORMATION */}
//       <section
//         className="card"
//         style={{ marginTop: 18 }}
//       >
//         <div className="detail-section-title">
//           <div>
//             <p className="small history-eyebrow">
//               MODEL INFORMATION
//             </p>

//             <h2>Evaluation summary</h2>
//           </div>

//           <span className="small muted">
//             {modelMetrics.testImages} test images
//           </span>
//         </div>

//         <div style={{ overflowX: "auto" }}>
//           <table>
//             <thead>
//               <tr>
//                 <th>Model</th>
//                 <th>Version</th>
//                 <th>Accuracy</th>
//                 <th>Macro Precision</th>
//                 <th>Macro Recall</th>
//                 <th>Macro F1</th>
//               </tr>
//             </thead>

//             <tbody>
//               <tr>
//                 <td>
//                   <strong>
//                     {modelMetrics.name}
//                   </strong>
//                 </td>

//                 <td>
//                   {modelMetrics.version}
//                 </td>

//                 <td>
//                   {modelMetrics.accuracy.toFixed(2)}%
//                 </td>

//                 <td>
//                   {modelMetrics.precision.toFixed(2)}%
//                 </td>

//                 <td>
//                   {modelMetrics.recall.toFixed(2)}%
//                 </td>

//                 <td>
//                   <strong>
//                     {modelMetrics.f1.toFixed(2)}%
//                   </strong>
//                 </td>
//               </tr>
//             </tbody>
//           </table>
//         </div>
//       </section>

//       {/* MODEL COMPARISON */}
// <section className="card" style={{ marginTop: 18 }}>
//   <div className="detail-section-title">
//     <div>
//       <p className="small history-eyebrow">
//         MODEL COMPARISON
//       </p>

//       <h2>Architecture comparison</h2>
//     </div>

//     <span className="small muted">
//       Same held-out test set
//     </span>
//   </div>

//   <p className="muted">
//     All models were evaluated using the same train, validation,
//     and held-out test split for a fair comparison.
//   </p>

//   <div style={{ overflowX: "auto", marginTop: 18 }}>
//     <table>
//       <thead>
//         <tr>
//           <th>Model</th>
//           <th>Accuracy</th>
//           <th>Macro Precision</th>
//           <th>Macro Recall</th>
//           <th>Macro F1</th>
//           <th>Inference</th>
//           <th>Selection</th>
//         </tr>
//       </thead>

//       <tbody>
//         {modelComparison.map((model) => (
//           <tr key={model.name}>
//             <td>
//               <strong>{model.name}</strong>
//             </td>

//             <td>
//               {model.accuracy.toFixed(2)}%
//             </td>

//             <td>
//               {model.precision.toFixed(2)}%
//             </td>

//             <td>
//               {model.recall.toFixed(2)}%
//             </td>

//             <td>
//               <strong>
//                 {model.f1.toFixed(2)}%
//               </strong>
//             </td>

//             <td>
//               {model.inference.toFixed(2)} ms
//             </td>

//             <td>
//               {model.selected ? (
//                 <span className="status confident">
//                   Selected
//                 </span>
//               ) : (
//                 <span className="small muted">
//                   Comparison
//                 </span>
//               )}
//             </td>
//           </tr>
//         ))}
//       </tbody>
//     </table>
//   </div>

//   <div className="warning" style={{ marginTop: 18 }}>
//     EfficientNet-B0 was selected as the primary wound-type model
//     because it achieved the highest overall Accuracy and Macro F1.
//     MobileNetV3-Small produced the fastest inference time, but with
//     lower overall classification performance.
//   </div>
// </section>

//       {/* PER CLASS PERFORMANCE */}
//       <section
//         className="card detail-scores"
//         style={{ marginTop: 18 }}
//       >
//         <div className="detail-section-title">
//           <div>
//             <p className="small history-eyebrow">
//               CLASS PERFORMANCE
//             </p>

//             <h2>Per-class F1 score</h2>
//           </div>

//           <span className="small muted">
//             {classMetrics.length} wound classes
//           </span>
//         </div>

//         {classMetrics.map((item, index) => (
//           <div
//             className="detail-score-row"
//             key={item.name}
//           >
//             <div className="detail-score-rank">
//               {index + 1}
//             </div>

//             <div className="detail-score-main">
//               <div className="scoreline">
//                 <span>
//                   {item.name}
//                 </span>

//                 <strong>
//                   {item.f1.toFixed(2)}%
//                 </strong>
//               </div>

//               <div className="bar">
//                 <span
//                   style={{
//                     width: `${item.f1}%`
//                   }}
//                 />
//               </div>
//             </div>
//           </div>
//         ))}
//       </section>

//       {/* RESEARCH FEATURES */}
//       <section
//         className="grid"
//         style={{ marginTop: 18 }}
//       >
//         <article className="card">
//           <p className="small history-eyebrow">
//             PRIMARY METRIC
//           </p>

//           <div className="kpi">
//             Macro F1
//           </div>

//           <p className="muted">
//             Gives equal importance to each wound class
//             when evaluating overall model performance.
//           </p>
//         </article>

//         <article className="card">
//           <p className="small history-eyebrow">
//             EXPLAINABILITY
//           </p>

//           <div className="kpi">
//             Grad-CAM
//           </div>

//           <p className="muted">
//             Heatmap visualization is implemented for
//             wound-type predictions.
//           </p>
//         </article>

//         <article className="card">
//           <p className="small history-eyebrow">
//             UNCERTAINTY
//           </p>

//           <div className="kpi">
//             60%
//           </div>

//           <p className="muted">
//             Wound-type predictions below the confidence
//             threshold are marked uncertain.
//           </p>
//         </article>
//       </section>

//       {/* DATASET & TRAINING METHODOLOGY */}
// <section className="card" style={{ marginTop: 18 }}>
//   <div className="detail-section-title">
//     <div>
//       <p className="small history-eyebrow">
//         RESEARCH METHODOLOGY
//       </p>

//       <h2>Dataset & training configuration</h2>
//     </div>

//     <span className="small muted">
//       wound-type-v1
//     </span>
//   </div>

//   <p className="muted">
//     The wound-type classifier was trained using transfer learning
//     with EfficientNet-B0 and evaluated using separate training,
//     validation, and held-out test datasets.
//   </p>

//   <div
//     className="grid"
//     style={{ marginTop: 18 }}
//   >
//     <article className="card">
//       <p className="small muted">ARCHITECTURE</p>
//       <div className="kpi">EfficientNet-B0</div>
//       <p className="muted">
//         ImageNet pretrained weights with a custom four-class
//         classification head.
//       </p>
//     </article>

//     <article className="card">
//       <p className="small muted">INPUT SIZE</p>
//       <div className="kpi">224 × 224</div>
//       <p className="muted">
//         RGB images normalized using ImageNet statistics.
//       </p>
//     </article>

//     <article className="card">
//       <p className="small muted">BATCH SIZE</p>
//       <div className="kpi">16</div>
//       <p className="muted">
//         Training samples processed in batches of sixteen.
//       </p>
//     </article>
//   </div>

//   <div style={{ overflowX: "auto", marginTop: 18 }}>
//     <table>
//       <tbody>
//         <tr>
//           <th>Classification task</th>
//           <td>4-class wound type classification</td>
//         </tr>

//         <tr>
//           <th>Classes</th>
//           <td>
//             Diabetic, Pressure, Surgical, Venous
//           </td>
//         </tr>

//         <tr>
//           <th>Architecture</th>
//           <td>EfficientNet-B0</td>
//         </tr>

//         <tr>
//           <th>Pretraining</th>
//           <td>ImageNet pretrained weights</td>
//         </tr>

//         <tr>
//           <th>Input resolution</th>
//           <td>224 × 224 RGB</td>
//         </tr>

//         <tr>
//           <th>Maximum epochs</th>
//           <td>20</td>
//         </tr>

//         <tr>
//           <th>Batch size</th>
//           <td>16</td>
//         </tr>

//         <tr>
//           <th>Optimizer</th>
//           <td>AdamW</td>
//         </tr>

//         <tr>
//           <th>Initial learning rate</th>
//           <td>0.0001</td>
//         </tr>

//         <tr>
//           <th>Weight decay</th>
//           <td>0.0001</td>
//         </tr>

//         <tr>
//           <th>Loss function</th>
//           <td>
//             Weighted Cross-Entropy Loss
//           </td>
//         </tr>

//         <tr>
//           <th>Early stopping</th>
//           <td>
//             5 epochs without validation Macro-F1 improvement
//           </td>
//         </tr>

//         <tr>
//           <th>Model selection</th>
//           <td>
//             Best validation Macro-F1
//           </td>
//         </tr>

//         <tr>
//           <th>Random seed</th>
//           <td>42</td>
//         </tr>

//         <tr>
//           <th>Primary evaluation metric</th>
//           <td>Macro F1</td>
//         </tr>
//       </tbody>
//     </table>
//   </div>
// </section>

//   {/* DATA AUGMENTATION */}
//   <section className="card" style={{ marginTop: 18 }}>
//     <div className="detail-section-title">
//       <div>
//         <p className="small history-eyebrow">
//           PREPROCESSING
//         </p>

//         <h2>Training data augmentation</h2>
//       </div>
//     </div>

//     <p className="muted">
//       Data augmentation was applied only to the training
//       dataset to improve model generalization.
//     </p>

//     <div
//       className="grid"
//       style={{ marginTop: 18 }}
//     >
//       <article className="card">
//         <p className="small muted">
//           HORIZONTAL FLIP
//         </p>

//         <div className="kpi">50%</div>

//         <p className="muted">
//           Random horizontal flipping with probability 0.5.
//         </p>
//       </article>

//       <article className="card">
//         <p className="small muted">
//           ROTATION
//         </p>

//         <div className="kpi">±10°</div>

//         <p className="muted">
//           Random image rotation during training.
//         </p>
//       </article>

//       <article className="card">
//         <p className="small muted">
//           COLOR JITTER
//         </p>

//         <div className="kpi">Enabled</div>

//         <p className="muted">
//           Small brightness, contrast, saturation and hue
//           variations.
//         </p>
//       </article>
//     </div>
//   </section>

//     {/* DATASET SPLIT */}
//   <section className="card" style={{ marginTop: 18 }}>
//     <div className="detail-section-title">
//       <div>
//         <p className="small history-eyebrow">
//           DATASET
//         </p>
//         <h2>Training, validation & test split</h2>
//       </div>

//       <span className="small muted">
//         {datasetMetrics.total} images
//       </span>
//     </div>

//     <div className="history-stats" style={{ marginTop: 18 }}>
//       <article className="card">
//         <p className="small muted">TRAINING</p>
//         <div className="kpi">{datasetMetrics.train}</div>
//         <p className="muted">Images used to optimize the model.</p>
//       </article>

//       <article className="card">
//         <p className="small muted">VALIDATION</p>
//         <div className="kpi">{datasetMetrics.validation}</div>
//         <p className="muted">
//           Used for model selection and early stopping.
//         </p>
//       </article>

//       <article className="card">
//         <p className="small muted">HELD-OUT TEST</p>
//         <div className="kpi">{datasetMetrics.test}</div>
//         <p className="muted">
//           Used only for final model evaluation.
//         </p>
//       </article>
//     </div>
//   </section>
//   {/* TRAINING HISTORY */}
// <section className="card" style={{ marginTop: 18 }}>
//   <div className="detail-section-title">
//     <div>
//       <p className="small history-eyebrow">
//         TRAINING HISTORY
//       </p>

//       <h2>Train vs validation Macro F1</h2>
//     </div>

//     <span className="small muted">
//       {trainingHistory.length} epochs
//     </span>
//   </div>

//   <p className="muted">
//     Training performance continued to improve while validation
//     performance peaked earlier, supporting the use of early stopping.
//   </p>
//   <TrainingHistoryChart />

//   {/* TRAINING HISTORY */}
// <section className="card" style={{ marginTop: 18 }}>
//   <div className="detail-section-title">
//     <div>
//       <p className="small history-eyebrow">
//         TRAINING HISTORY
//       </p>

//       <h2>Train vs validation Macro F1</h2>
//     </div>

//     <span className="small muted">
//       {trainingHistory.length} epochs
//     </span>
//   </div>

//   <p className="muted">
//     Training performance continued to improve while validation
//     performance peaked earlier, supporting the use of early stopping.
//   </p>

//   <TrainingHistoryChart />

//   <div style={{ overflowX: "auto", marginTop: 18 }}>
//     <table>
//       <thead>
//         <tr>
//           <th>Epoch</th>
//           <th>Train Macro F1</th>
//           <th>Validation Macro F1</th>
//         </tr>
//       </thead>

//       <tbody>
//         {trainingHistory.map((item) => (
//           <tr key={item.epoch}>
//             <td>
//               <strong>{item.epoch}</strong>
//             </td>

//             <td>{item.trainF1.toFixed(2)}%</td>

//             <td>
//               <strong>{item.valF1.toFixed(2)}%</strong>
//             </td>
//           </tr>
//         ))}
//       </tbody>
//     </table>
//   </div>
// </section>

// {/* TRAINING OUTCOME */}
// <section className="card" style={{ marginTop: 18 }}></section>

//   <div style={{ overflowX: "auto", marginTop: 18 }}>
//     <table>
//       <thead>
//         <tr>
//           <th>Epoch</th>
//           <th>Train Macro F1</th>
//           <th>Validation Macro F1</th>
//         </tr>
//       </thead>

//       <tbody>
//         {trainingHistory.map((item) => (
//           <tr key={item.epoch}>
//             <td>
//               <strong>{item.epoch}</strong>
//             </td>

//             <td>
//               {item.trainF1.toFixed(2)}%
//             </td>

//             <td>
//               <strong>
//                 {item.valF1.toFixed(2)}%
//               </strong>
//             </td>
//           </tr>
//         ))}
//       </tbody>
//     </table>
//   </div>
// </section>
//   {/* TRAINING OUTCOME */}
//   <section className="card" style={{ marginTop: 18 }}>
//     <div className="detail-section-title">
//       <div>
//         <p className="small history-eyebrow">
//           TRAINING OUTCOME
//         </p>
//         <h2>Optimization summary</h2>
//       </div>
//     </div>

//     <div className="grid" style={{ marginTop: 18 }}>
//       <article className="card">
//         <p className="small muted">BEST VALIDATION F1</p>
//         <div className="kpi">
//           {datasetMetrics.bestValidationF1.toFixed(2)}%
//         </div>
//         <p className="muted">
//           Best validation Macro F1 reached during training.
//         </p>
//       </article>

//       <article className="card">
//         <p className="small muted">BEST EPOCH</p>
//         <div className="kpi">{datasetMetrics.bestEpoch}</div>
//         <p className="muted">
//           Epoch where the best validation checkpoint was saved.
//         </p>
//       </article>

//       <article className="card">
//         <p className="small muted">EPOCHS RUN</p>
//         <div className="kpi">{datasetMetrics.epochsRun}</div>
//         <p className="muted">
//           Training stopped after {datasetMetrics.epochsRun} epochs using
//           early stopping based on validation Macro F1.
//         </p>
//       </article>

//       <article className="card">
//         <p className="small muted">INFERENCE TIME</p>
//         <div className="kpi">
//           {datasetMetrics.inferenceMs.toFixed(2)} ms
//         </div>
//         <p className="muted">
//           Average inference time per held-out test image.
//         </p>
//       </article>
//     </div>
//   </section>

//       {/* CONFUSION MATRIX */}
//       <section
//         className="card"
//         style={{ marginTop: 18 }}
//       >
//         <div className="detail-section-title">
//           <div>
//             <p className="small history-eyebrow">
//               ERROR ANALYSIS
//             </p>

//             <h2>Confusion matrix</h2>
//           </div>

//           <span className="small muted">
//             Held-out test set
//           </span>
//         </div>

//         <p className="muted">
//           Rows represent the actual wound type and columns
//           represent the model prediction.
//         </p>

//         <div
//           style={{
//             overflowX: "auto",
//             marginTop: 18
//           }}
//         >
//           <table>
//             <thead>
//               <tr>
//                 <th>
//                   Actual ↓ / Predicted →
//                 </th>

//                 {confusionMatrix.labels.map((label) => (
//                   <th key={label}>
//                     {label}
//                   </th>
//                 ))}
//               </tr>
//             </thead>

//             <tbody>
//               {confusionMatrix.values.map(
//                 (row, rowIndex) => (
//                   <tr
//                     key={
//                       confusionMatrix.labels[rowIndex]
//                     }
//                   >
//                     <td>
//                       <strong>
//                         {
//                           confusionMatrix.labels[
//                             rowIndex
//                           ]
//                         }
//                       </strong>
//                     </td>

//                     {row.map(
//                       (value, columnIndex) => (
//                         <td key={columnIndex}>
//                           <strong>
//                             {value}
//                           </strong>
//                         </td>
//                       )
//                     )}
//                   </tr>
//                 )
//               )}
//             </tbody>
//           </table>
//         </div>

//         <p
//           className="muted"
//           style={{ marginTop: 16 }}
//         >
//           The confusion matrix shows how the model
//           classified each wound type in the held-out
//           test dataset.
//         </p>
//       </section>

//       {/* DISCLAIMER */}
//       <section
//         className="warning"
//         style={{ marginTop: 18 }}
//       >
//         Research and decision-support system only.
//         Performance metrics represent experimental model
//         evaluation and should not be interpreted as clinical
//         diagnostic performance.
//       </section>
//     </>
//   );
// }
const trainingHistory = [
  { epoch: 1, trainF1: 43.50, valF1: 51.50 },
  { epoch: 2, trainF1: 71.51, valF1: 54.38 },
  { epoch: 3, trainF1: 73.89, valF1: 62.14 },
  { epoch: 4, trainF1: 82.44, valF1: 61.97 },
  { epoch: 5, trainF1: 85.98, valF1: 65.69 },
  { epoch: 6, trainF1: 89.77, valF1: 66.31 },
  { epoch: 7, trainF1: 92.43, valF1: 65.24 },
  { epoch: 8, trainF1: 95.03, valF1: 64.86 },
  { epoch: 9, trainF1: 95.14, valF1: 64.31 },
  { epoch: 10, trainF1: 94.47, valF1: 64.63 },
  { epoch: 11, trainF1: 97.21, valF1: 64.46 }
];
const modelComparison = [
  {
    name: "EfficientNet-B0",
    accuracy: 75.96,
    precision: 75.08,
    recall: 74.47,
    f1: 74.58,
    inference: 18.95,
    selected: true
  },
  {
    name: "ResNet18",
    accuracy: 74.04,
    precision: 73.25,
    recall: 72.89,
    f1: 72.72,
    inference: 17.04,
    selected: false
  },
  {
    name: "MobileNetV3-Small",
    accuracy: 72.12,
    precision: 71.29,
    recall: 70.45,
    f1: 70.35,
    inference: 2.88,
    selected: false
  }
];
const datasetMetrics = {
  train: 508,
  validation: 117,
  test: 104,
  total: 729,
  bestValidationF1: 66.31,
  inferenceMs: 18.95,
  epochsRun: 11,
  bestEpoch: 6
};

const modelMetrics = {
  name: "EfficientNet-B0",
  version: "wound-type-v1",
  accuracy: 75.96,
  precision: 75.08,
  recall: 74.47,
  f1: 74.58,
  testImages: 104
};

const classMetrics = [
  { name: "Diabetic", f1: 74.07 },
  { name: "Pressure", f1: 63.41 },
  { name: "Surgical", f1: 75.56 },
  { name: "Venous", f1: 85.29 }
];

const confusionMatrix = {
  labels: ["Diabetic", "Pressure", "Surgical", "Venous"],
  values: [
    [20, 4, 1, 3],
    [4, 13, 1, 2],
    [2, 3, 17, 2],
    [0, 1, 2, 29]
  ]
};
function TrainingHistoryChart() {
  const width = 900;
  const height = 320;
  const padding = 50;

  const maxEpoch = Math.max(...trainingHistory.map((d) => d.epoch));
  const minF1 = 40;
  const maxF1 = 100;

  const xScale = (epoch: number) =>
    padding +
    ((epoch - 1) / (maxEpoch - 1)) *
      (width - padding * 2);

  const yScale = (value: number) =>
    height -
    padding -
    ((value - minF1) / (maxF1 - minF1)) *
      (height - padding * 2);

  const trainPoints = trainingHistory
    .map((d) => `${xScale(d.epoch)},${yScale(d.trainF1)}`)
    .join(" ");

  const valPoints = trainingHistory
    .map((d) => `${xScale(d.epoch)},${yScale(d.valF1)}`)
    .join(" ");

  return (
    <div style={{ overflowX: "auto", marginTop: 18 }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", minWidth: 700 }}
      >
        {/* Y-axis labels */}
        {[40, 50, 60, 70, 80, 90, 100].map((value) => (
          <g key={value}>
            <line
              x1={padding}
              x2={width - padding}
              y1={yScale(value)}
              y2={yScale(value)}
              stroke="#e5e7eb"
            />
            <text
              x={10}
              y={yScale(value) + 4}
              fontSize="12"
              fill="#6b7280"
            >
              {value}%
            </text>
          </g>
        ))}

        {/* X-axis labels */}
        {trainingHistory.map((d) => (
          <text
            key={d.epoch}
            x={xScale(d.epoch)}
            y={height - 15}
            textAnchor="middle"
            fontSize="12"
            fill="#6b7280"
          >
            {d.epoch}
          </text>
        ))}

        {/* Train line */}
        <polyline
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          points={trainPoints}
        />

        {/* Validation line */}
        <polyline
          fill="none"
          stroke="#7c3aed"
          strokeWidth="3"
          points={valPoints}
        />

        {/* Best epoch marker */}
        <line
          x1={xScale(datasetMetrics.bestEpoch)}
          x2={xScale(datasetMetrics.bestEpoch)}
          y1={padding}
          y2={height - padding}
          stroke="#ef4444"
          strokeDasharray="5 5"
        />

        <text
          x={xScale(datasetMetrics.bestEpoch) + 8}
          y={padding + 14}
          fontSize="12"
          fill="#ef4444"
        >
          Best epoch {datasetMetrics.bestEpoch}
        </text>
      </svg>

      <div
        style={{
          display: "flex",
          gap: 18,
          marginTop: 10,
          flexWrap: "wrap"
        }}
      >
        <span className="small muted">
          Train Macro F1
        </span>

        <span className="small muted">
          Validation Macro F1
        </span>

        <span className="small muted">
          Best validation epoch
        </span>
      </div>
    </div>
  );
}
export default function ResearchPage() {
  return (
    <>
      {/* HEADER */}
      <section className="card">
        <p className="small history-eyebrow">
          RESEARCH DASHBOARD
        </p>

        <h1>Wound Type Model Evaluation</h1>

        <p className="muted">
          Evaluation results for the trained multi-class wound
          classification model using the held-out test dataset.
        </p>

        <div
          style={{
            marginTop: 18,
            display: "flex",
            gap: 12,
            flexWrap: "wrap"
          }}
        >
          <span className="status confident">
            EfficientNet-B0
          </span>

          <span className="status confident">
            wound-type-v1
          </span>

          <span className="status confident">
            Research
          </span>
        </div>
      </section>

      {/* MAIN METRICS */}
      <section
        className="history-stats"
        style={{ marginTop: 18 }}
      >
        <article className="card">
          <p className="small muted">
            ACCURACY
          </p>

          <div className="kpi">
            {modelMetrics.accuracy.toFixed(2)}%
          </div>

          <p className="muted">
            Overall correctly classified test images.
          </p>
        </article>

        <article className="card">
          <p className="small muted">
            MACRO PRECISION
          </p>

          <div className="kpi">
            {modelMetrics.precision.toFixed(2)}%
          </div>

          <p className="muted">
            Average precision across all wound classes.
          </p>
        </article>

        <article className="card">
          <p className="small muted">
            MACRO RECALL
          </p>

          <div className="kpi">
            {modelMetrics.recall.toFixed(2)}%
          </div>

          <p className="muted">
            Average recall across all wound classes.
          </p>
        </article>

        <article className="card">
          <p className="small muted">
            MACRO F1
          </p>

          <div className="kpi">
            {modelMetrics.f1.toFixed(2)}%
          </div>

          <p className="muted">
            Primary balanced performance metric.
          </p>
        </article>
      </section>

      {/* MODEL INFORMATION */}
      <section
        className="card"
        style={{ marginTop: 18 }}
      >
        <div className="detail-section-title">
          <div>
            <p className="small history-eyebrow">
              MODEL INFORMATION
            </p>

            <h2>Evaluation summary</h2>
          </div>

          <span className="small muted">
            {modelMetrics.testImages} test images
          </span>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Version</th>
                <th>Accuracy</th>
                <th>Macro Precision</th>
                <th>Macro Recall</th>
                <th>Macro F1</th>
              </tr>
            </thead>

            <tbody>
              <tr>
                <td>
                  <strong>
                    {modelMetrics.name}
                  </strong>
                </td>

                <td>
                  {modelMetrics.version}
                </td>

                <td>
                  {modelMetrics.accuracy.toFixed(2)}%
                </td>

                <td>
                  {modelMetrics.precision.toFixed(2)}%
                </td>

                <td>
                  {modelMetrics.recall.toFixed(2)}%
                </td>

                <td>
                  <strong>
                    {modelMetrics.f1.toFixed(2)}%
                  </strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* MODEL COMPARISON */}
<section className="card" style={{ marginTop: 18 }}>
  <div className="detail-section-title">
    <div>
      <p className="small history-eyebrow">
        MODEL COMPARISON
      </p>

      <h2>Architecture comparison</h2>
    </div>

    <span className="small muted">
      Same held-out test set
    </span>
  </div>

  <p className="muted">
    All models were evaluated using the same train, validation,
    and held-out test split for a fair comparison.
  </p>

  <div style={{ overflowX: "auto", marginTop: 18 }}>
    <table>
      <thead>
        <tr>
          <th>Model</th>
          <th>Accuracy</th>
          <th>Macro Precision</th>
          <th>Macro Recall</th>
          <th>Macro F1</th>
          <th>Inference</th>
          <th>Selection</th>
        </tr>
      </thead>

      <tbody>
        {modelComparison.map((model) => (
          <tr key={model.name}>
            <td>
              <strong>{model.name}</strong>
            </td>

            <td>
              {model.accuracy.toFixed(2)}%
            </td>

            <td>
              {model.precision.toFixed(2)}%
            </td>

            <td>
              {model.recall.toFixed(2)}%
            </td>

            <td>
              <strong>
                {model.f1.toFixed(2)}%
              </strong>
            </td>

            <td>
              {model.inference.toFixed(2)} ms
            </td>

            <td>
              {model.selected ? (
                <span className="status confident">
                  Selected
                </span>
              ) : (
                <span className="small muted">
                  Comparison
                </span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>

  <div className="warning" style={{ marginTop: 18 }}>
    EfficientNet-B0 was selected as the primary wound-type model
    because it achieved the highest overall Accuracy and Macro F1.
    MobileNetV3-Small produced the fastest inference time, but with
    lower overall classification performance.
  </div>
</section>

      {/* PER CLASS PERFORMANCE */}
      <section
        className="card detail-scores"
        style={{ marginTop: 18 }}
      >
        <div className="detail-section-title">
          <div>
            <p className="small history-eyebrow">
              CLASS PERFORMANCE
            </p>

            <h2>Per-class F1 score</h2>
          </div>

          <span className="small muted">
            {classMetrics.length} wound classes
          </span>
        </div>

        {classMetrics.map((item, index) => (
          <div
            className="detail-score-row"
            key={item.name}
          >
            <div className="detail-score-rank">
              {index + 1}
            </div>

            <div className="detail-score-main">
              <div className="scoreline">
                <span>
                  {item.name}
                </span>

                <strong>
                  {item.f1.toFixed(2)}%
                </strong>
              </div>

              <div className="bar">
                <span
                  style={{
                    width: `${item.f1}%`
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </section>

      {/* RESEARCH FEATURES */}
      <section
        className="grid"
        style={{ marginTop: 18 }}
      >
        <article className="card">
          <p className="small history-eyebrow">
            PRIMARY METRIC
          </p>

          <div className="kpi">
            Macro F1
          </div>

          <p className="muted">
            Gives equal importance to each wound class
            when evaluating overall model performance.
          </p>
        </article>

        <article className="card">
          <p className="small history-eyebrow">
            EXPLAINABILITY
          </p>

          <div className="kpi">
            Grad-CAM
          </div>

          <p className="muted">
            Heatmap visualization is implemented for
            wound-type predictions.
          </p>
        </article>

        <article className="card">
          <p className="small history-eyebrow">
            UNCERTAINTY
          </p>

          <div className="kpi">
            60%
          </div>

          <p className="muted">
            Wound-type predictions below the confidence
            threshold are marked uncertain.
          </p>
        </article>
      </section>

      {/* DATASET & TRAINING METHODOLOGY */}
<section className="card" style={{ marginTop: 18 }}>
  <div className="detail-section-title">
    <div>
      <p className="small history-eyebrow">
        RESEARCH METHODOLOGY
      </p>

      <h2>Dataset & training configuration</h2>
    </div>

    <span className="small muted">
      wound-type-v1
    </span>
  </div>

  <p className="muted">
    The wound-type classifier was trained using transfer learning
    with EfficientNet-B0 and evaluated using separate training,
    validation, and held-out test datasets.
  </p>

  <div
    className="grid"
    style={{ marginTop: 18 }}
  >
    <article className="card">
      <p className="small muted">ARCHITECTURE</p>
      <div className="kpi">EfficientNet-B0</div>
      <p className="muted">
        ImageNet pretrained weights with a custom four-class
        classification head.
      </p>
    </article>

    <article className="card">
      <p className="small muted">INPUT SIZE</p>
      <div className="kpi">224 × 224</div>
      <p className="muted">
        RGB images normalized using ImageNet statistics.
      </p>
    </article>

    <article className="card">
      <p className="small muted">BATCH SIZE</p>
      <div className="kpi">16</div>
      <p className="muted">
        Training samples processed in batches of sixteen.
      </p>
    </article>
  </div>

  <div style={{ overflowX: "auto", marginTop: 18 }}>
    <table>
      <tbody>
        <tr>
          <th>Classification task</th>
          <td>4-class wound type classification</td>
        </tr>

        <tr>
          <th>Classes</th>
          <td>
            Diabetic, Pressure, Surgical, Venous
          </td>
        </tr>

        <tr>
          <th>Architecture</th>
          <td>EfficientNet-B0</td>
        </tr>

        <tr>
          <th>Pretraining</th>
          <td>ImageNet pretrained weights</td>
        </tr>

        <tr>
          <th>Input resolution</th>
          <td>224 × 224 RGB</td>
        </tr>

        <tr>
          <th>Maximum epochs</th>
          <td>20</td>
        </tr>

        <tr>
          <th>Batch size</th>
          <td>16</td>
        </tr>

        <tr>
          <th>Optimizer</th>
          <td>AdamW</td>
        </tr>

        <tr>
          <th>Initial learning rate</th>
          <td>0.0001</td>
        </tr>

        <tr>
          <th>Weight decay</th>
          <td>0.0001</td>
        </tr>

        <tr>
          <th>Loss function</th>
          <td>
            Weighted Cross-Entropy Loss
          </td>
        </tr>

        <tr>
          <th>Early stopping</th>
          <td>
            5 epochs without validation Macro-F1 improvement
          </td>
        </tr>

        <tr>
          <th>Model selection</th>
          <td>
            Best validation Macro-F1
          </td>
        </tr>

        <tr>
          <th>Random seed</th>
          <td>42</td>
        </tr>

        <tr>
          <th>Primary evaluation metric</th>
          <td>Macro F1</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>

  {/* DATA AUGMENTATION */}
  <section className="card" style={{ marginTop: 18 }}>
    <div className="detail-section-title">
      <div>
        <p className="small history-eyebrow">
          PREPROCESSING
        </p>

        <h2>Training data augmentation</h2>
      </div>
    </div>

    <p className="muted">
      Data augmentation was applied only to the training
      dataset to improve model generalization.
    </p>

    <div
      className="grid"
      style={{ marginTop: 18 }}
    >
      <article className="card">
        <p className="small muted">
          HORIZONTAL FLIP
        </p>

        <div className="kpi">50%</div>

        <p className="muted">
          Random horizontal flipping with probability 0.5.
        </p>
      </article>

      <article className="card">
        <p className="small muted">
          ROTATION
        </p>

        <div className="kpi">±10°</div>

        <p className="muted">
          Random image rotation during training.
        </p>
      </article>

      <article className="card">
        <p className="small muted">
          COLOR JITTER
        </p>

        <div className="kpi">Enabled</div>

        <p className="muted">
          Small brightness, contrast, saturation and hue
          variations.
        </p>
      </article>
    </div>
  </section>

    {/* DATASET SPLIT */}
  <section className="card" style={{ marginTop: 18 }}>
    <div className="detail-section-title">
      <div>
        <p className="small history-eyebrow">
          DATASET
        </p>
        <h2>Training, validation & test split</h2>
      </div>

      <span className="small muted">
        {datasetMetrics.total} images
      </span>
    </div>

    <div className="history-stats" style={{ marginTop: 18 }}>
      <article className="card">
        <p className="small muted">TRAINING</p>
        <div className="kpi">{datasetMetrics.train}</div>
        <p className="muted">Images used to optimize the model.</p>
      </article>

      <article className="card">
        <p className="small muted">VALIDATION</p>
        <div className="kpi">{datasetMetrics.validation}</div>
        <p className="muted">
          Used for model selection and early stopping.
        </p>
      </article>

      <article className="card">
        <p className="small muted">HELD-OUT TEST</p>
        <div className="kpi">{datasetMetrics.test}</div>
        <p className="muted">
          Used only for final model evaluation.
        </p>
      </article>
    </div>
  </section>
      {/* TRAINING HISTORY */}
      <section
        className="card"
        style={{ marginTop: 18 }}
      >
        <div className="detail-section-title">
          <div>
            <p className="small history-eyebrow">
              TRAINING HISTORY
            </p>

            <h2>Train vs validation Macro F1</h2>
          </div>

          <span className="small muted">
            {trainingHistory.length} epochs
          </span>
        </div>

        <p className="muted">
          Training performance continued to improve while validation
          performance peaked earlier, supporting the use of early stopping.
        </p>

        <TrainingHistoryChart />

        <div style={{ overflowX: "auto", marginTop: 18 }}>
          <table>
            <thead>
              <tr>
                <th>Epoch</th>
                <th>Train Macro F1</th>
                <th>Validation Macro F1</th>
              </tr>
            </thead>

            <tbody>
              {trainingHistory.map((item) => (
                <tr key={item.epoch}>
                  <td>
                    <strong>{item.epoch}</strong>
                  </td>

                  <td>{item.trainF1.toFixed(2)}%</td>

                  <td>
                    <strong>{item.valF1.toFixed(2)}%</strong>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
  {/* TRAINING OUTCOME */}
  <section className="card" style={{ marginTop: 18 }}>
    <div className="detail-section-title">
      <div>
        <p className="small history-eyebrow">
          TRAINING OUTCOME
        </p>
        <h2>Optimization summary</h2>
      </div>
    </div>

    <div className="grid" style={{ marginTop: 18 }}>
      <article className="card">
        <p className="small muted">BEST VALIDATION F1</p>
        <div className="kpi">
          {datasetMetrics.bestValidationF1.toFixed(2)}%
        </div>
        <p className="muted">
          Best validation Macro F1 reached during training.
        </p>
      </article>

      <article className="card">
        <p className="small muted">BEST EPOCH</p>
        <div className="kpi">{datasetMetrics.bestEpoch}</div>
        <p className="muted">
          Epoch where the best validation checkpoint was saved.
        </p>
      </article>

      <article className="card">
        <p className="small muted">EPOCHS RUN</p>
        <div className="kpi">{datasetMetrics.epochsRun}</div>
        <p className="muted">
          Training stopped after {datasetMetrics.epochsRun} epochs using
          early stopping based on validation Macro F1.
        </p>
      </article>

      <article className="card">
        <p className="small muted">INFERENCE TIME</p>
        <div className="kpi">
          {datasetMetrics.inferenceMs.toFixed(2)} ms
        </div>
        <p className="muted">
          Average inference time per held-out test image.
        </p>
      </article>
    </div>
  </section>

      {/* CONFUSION MATRIX */}
      <section
        className="card"
        style={{ marginTop: 18 }}
      >
        <div className="detail-section-title">
          <div>
            <p className="small history-eyebrow">
              ERROR ANALYSIS
            </p>

            <h2>Confusion matrix</h2>
          </div>

          <span className="small muted">
            Held-out test set
          </span>
        </div>

        <p className="muted">
          Rows represent the actual wound type and columns
          represent the model prediction.
        </p>

        <div
          style={{
            overflowX: "auto",
            marginTop: 18
          }}
        >
          <table>
            <thead>
              <tr>
                <th>
                  Actual ↓ / Predicted →
                </th>

                {confusionMatrix.labels.map((label) => (
                  <th key={label}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {confusionMatrix.values.map(
                (row, rowIndex) => (
                  <tr
                    key={
                      confusionMatrix.labels[rowIndex]
                    }
                  >
                    <td>
                      <strong>
                        {
                          confusionMatrix.labels[
                            rowIndex
                          ]
                        }
                      </strong>
                    </td>

                    {row.map(
                      (value, columnIndex) => (
                        <td key={columnIndex}>
                          <strong>
                            {value}
                          </strong>
                        </td>
                      )
                    )}
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>

        <p
          className="muted"
          style={{ marginTop: 16 }}
        >
          The confusion matrix shows how the model
          classified each wound type in the held-out
          test dataset.
        </p>
      </section>

      {/* DISCLAIMER */}
      <section
        className="warning"
        style={{ marginTop: 18 }}
      >
        Research and decision-support system only.
        Performance metrics represent experimental model
        evaluation and should not be interpreted as clinical
        diagnostic performance.
      </section>
    </>
  );
}