import { useState } from "react";
import type {
  EvidenceSummaryItem,
  FileReferenceSummaryItem,
  M17KnowledgeData,
  MemorySummaryItem
} from "../api/types";
import { EmptyState } from "./DataState";

export function EvidenceViewerPanel({ knowledge }: { knowledge: M17KnowledgeData }) {
  const [selectedRef, setSelectedRef] = useState(knowledge.evidence[0]?.evidenceRef ?? "");
  const selected = knowledge.evidence.find((item) => item.evidenceRef === selectedRef) ?? knowledge.evidence[0];

  return (
    <section className="page-section" aria-labelledby="evidence-viewer-heading">
      <ViewerHeading
        eyebrow="M17 knowledge surface"
        headingId="evidence-viewer-heading"
        heading="Evidence Viewer"
        status="redacted summary-only"
        copy="Evidence views are read-only. They show governed evidence refs, provenance summaries, and related refs without exposing source material."
      />
      <BoundaryNotice knowledge={knowledge} />
      {knowledge.evidence.length > 0 && selected ? (
        <div className="review-layout">
          <div className="review-list" aria-label="Evidence summaries">
            {knowledge.evidence.map((item) => (
              <EvidenceRow
                key={item.evidenceRef}
                item={item}
                selected={item.evidenceRef === selected.evidenceRef}
                onSelect={setSelectedRef}
              />
            ))}
          </div>
          <EvidenceDetail item={selected} />
        </div>
      ) : (
        <EmptyState title="No evidence summaries" message="No redacted evidence summaries are available." />
      )}
    </section>
  );
}

export function FileReferenceViewerPanel({ knowledge }: { knowledge: M17KnowledgeData }) {
  const [selectedRef, setSelectedRef] = useState(knowledge.fileRefs[0]?.fileRef ?? "");
  const selected = knowledge.fileRefs.find((item) => item.fileRef === selectedRef) ?? knowledge.fileRefs[0];

  return (
    <section className="page-section" aria-labelledby="file-ref-viewer-heading">
      <ViewerHeading
        eyebrow="M17 knowledge surface"
        headingId="file-ref-viewer-heading"
        heading="File Reference Viewer"
        status="metadata-only"
        copy="File ref views are read-only. They show safe file labels, classifications, and related refs without exposing file body text."
      />
      <p className="safe-copy">File writes are not available from this UI. No filesystem browsing is available.</p>
      <BoundaryNotice knowledge={knowledge} />
      {knowledge.fileRefs.length > 0 && selected ? (
        <div className="review-layout">
          <div className="review-list" aria-label="File ref summaries">
            {knowledge.fileRefs.map((item) => (
              <FileRefRow
                key={item.fileRef}
                item={item}
                selected={item.fileRef === selected.fileRef}
                onSelect={setSelectedRef}
              />
            ))}
          </div>
          <FileRefDetail item={selected} />
        </div>
      ) : (
        <EmptyState title="No file ref summaries" message="No redacted file ref summaries are available." />
      )}
    </section>
  );
}

export function MemoryViewerPanel({ knowledge }: { knowledge: M17KnowledgeData }) {
  const [selectedRef, setSelectedRef] = useState(knowledge.memories[0]?.memoryRef ?? "");
  const selected = knowledge.memories.find((item) => item.memoryRef === selectedRef) ?? knowledge.memories[0];

  return (
    <section className="page-section" aria-labelledby="memory-viewer-heading">
      <ViewerHeading
        eyebrow="M17 knowledge surface"
        headingId="memory-viewer-heading"
        heading="Memory Viewer"
        status="recall-only"
        copy="Memory is recall, not authority. Canonical files and governed source systems outrank memory."
      />
      <BoundaryNotice knowledge={knowledge} />
      {knowledge.memories.length > 0 && selected ? (
        <div className="review-layout">
          <div className="review-list" aria-label="Memory summaries">
            {knowledge.memories.map((item) => (
              <MemoryRow
                key={item.memoryRef}
                item={item}
                selected={item.memoryRef === selected.memoryRef}
                onSelect={setSelectedRef}
              />
            ))}
          </div>
          <MemoryDetail item={selected} />
        </div>
      ) : (
        <EmptyState title="No memory summaries" message="No redacted memory summaries are available." />
      )}
    </section>
  );
}

function ViewerHeading({
  eyebrow,
  headingId,
  heading,
  status,
  copy
}: {
  eyebrow: string;
  headingId: string;
  heading: string;
  status: string;
  copy: string;
}) {
  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2 id={headingId}>{heading}</h2>
        </div>
        <span className="status-pill compact">{status}</span>
      </div>
      <p className="section-copy">{copy}</p>
    </>
  );
}

function BoundaryNotice({ knowledge }: { knowledge: M17KnowledgeData }) {
  return (
    <>
      <p className="safe-copy">{knowledge.boundarySummary}</p>
      <div className="note-list" aria-label="M17 knowledge warnings">
        {knowledge.warningCodes.map((code) => (
          <span key={code}>{code}</span>
        ))}
      </div>
    </>
  );
}

function EvidenceRow({
  item,
  selected,
  onSelect
}: {
  item: EvidenceSummaryItem;
  selected: boolean;
  onSelect: (evidenceRef: string) => void;
}) {
  return (
    <article className={`review-card${selected ? " selected" : ""}`} aria-current={selected ? "true" : undefined}>
      <div className="review-card-heading">
        <h3>{item.evidenceRef}</h3>
        <span>{item.confidenceStatus}</span>
      </div>
      <p>{item.evidenceType}</p>
      <p className="review-meta">
        {item.redactionStatus} | {item.timestamp}
      </p>
      <button type="button" className="secondary-button" onClick={() => onSelect(item.evidenceRef)}>
        View metadata
      </button>
    </article>
  );
}

function FileRefRow({
  item,
  selected,
  onSelect
}: {
  item: FileReferenceSummaryItem;
  selected: boolean;
  onSelect: (fileRef: string) => void;
}) {
  return (
    <article className={`review-card${selected ? " selected" : ""}`} aria-current={selected ? "true" : undefined}>
      <div className="review-card-heading">
        <h3>{item.fileRef}</h3>
        <span>{item.fileKind}</span>
      </div>
      <p>Safe file label: {item.safeFilename}</p>
      <p className="review-meta">
        {item.redactionStatus} | {item.sizeSummary}
      </p>
      <button type="button" className="secondary-button" onClick={() => onSelect(item.fileRef)}>
        View metadata
      </button>
    </article>
  );
}

function MemoryRow({
  item,
  selected,
  onSelect
}: {
  item: MemorySummaryItem;
  selected: boolean;
  onSelect: (memoryRef: string) => void;
}) {
  return (
    <article className={`review-card${selected ? " selected" : ""}`} aria-current={selected ? "true" : undefined}>
      <div className="review-card-heading">
        <h3>{item.memoryRef}</h3>
        <span>{item.reviewStatus}</span>
      </div>
      <p>{item.memoryType}</p>
      <p className="review-meta">stale review | source conflict flagged</p>
      <button type="button" className="secondary-button" onClick={() => onSelect(item.memoryRef)}>
        View metadata
      </button>
    </article>
  );
}

function EvidenceDetail({ item }: { item: EvidenceSummaryItem }) {
  return (
    <article className="panel review-detail" aria-label="Evidence detail">
      <PanelHeading eyebrow="Selected evidence" heading={item.evidenceRef} status={item.confidenceStatus} />
      <dl className="detail-grid">
        <DetailTerm label="Evidence type" value={item.evidenceType} />
        <DetailTerm label="Source type" value={item.sourceType} />
        <DetailTerm label="Source ref" value={item.sourceRef} />
        <DetailTerm label="Data classification" value={item.dataClassification} />
        <DetailTerm label="Redaction status" value={item.redactionStatus} />
        <DetailTerm label="Timestamp" value={item.timestamp} />
        <DetailTerm label="Provenance summary" value={item.provenanceSummary} />
      </dl>
      <TagList label="Claim refs" values={item.claimRefs} />
      <TagList label="Event refs" values={item.eventRefs} />
      <TagList label="Receipt refs" values={item.receiptRefs} />
      <TagList label="File refs" values={item.fileRefs} />
      <TagList label="Memory refs" values={item.memoryRefs} />
      <p className="safe-copy">Evidence detail is redacted summary metadata only.</p>
      <p className="safe-copy">{item.safeSummary}</p>
    </article>
  );
}

function FileRefDetail({ item }: { item: FileReferenceSummaryItem }) {
  return (
    <article className="panel review-detail" aria-label="File ref detail">
      <PanelHeading eyebrow="Selected file ref" heading={item.fileRef} status={item.fileKind} />
      <dl className="detail-grid">
        <DetailTerm label="Safe filename" value={item.safeFilename} />
        <DetailTerm label="File kind" value={item.fileKind} />
        <DetailTerm label="Size summary" value={item.sizeSummary} />
        <DetailTerm label="Data classification" value={item.dataClassification} />
        <DetailTerm label="Source surface" value={item.sourceSurface} />
        <DetailTerm label="Redaction status" value={item.redactionStatus} />
        <DetailTerm label="Path disclosure" value={item.pathDisclosure} />
      </dl>
      <TagList label="Event refs" values={item.eventRefs} />
      <TagList label="Receipt refs" values={item.receiptRefs} />
      <TagList label="Evidence refs" values={item.evidenceRefs} />
      <p className="safe-copy">File ref detail is redacted summary metadata only.</p>
      <p className="safe-copy">{item.safeMetadataSummary}</p>
    </article>
  );
}

function MemoryDetail({ item }: { item: MemorySummaryItem }) {
  return (
    <article className="panel review-detail" aria-label="Memory detail">
      <PanelHeading eyebrow="Selected memory" heading={item.memoryRef} status={item.reviewStatus} />
      <dl className="detail-grid">
        <DetailTerm label="Memory type" value={item.memoryType} />
        <DetailTerm label="Confidence" value={item.confidenceStatus} />
        <DetailTerm label="Review status" value={item.reviewStatus} />
        <DetailTerm label="Staleness" value={item.staleStatus} />
        <DetailTerm label="Conflict indicator" value={item.conflictStatus.replace("Conflict indicator: ", "")} />
        <DetailTerm label="Data classification" value={item.dataClassification} />
        <DetailTerm label="Redaction status" value={item.redactionStatus} />
      </dl>
      <TagList label="Source refs" values={item.sourceRefs} />
      <TagList label="Related event refs" values={item.relatedEventRefs} />
      <TagList label="Related receipt refs" values={item.relatedReceiptRefs} />
      <TagList label="Related evidence refs" values={item.relatedEvidenceRefs} />
      <p className="safe-copy">Memory detail is redacted summary metadata only.</p>
      <p className="safe-copy">{item.authorityNotice}</p>
      <p className="safe-copy">{item.safeSummary}</p>
    </article>
  );
}

function PanelHeading({ eyebrow, heading, status }: { eyebrow: string; heading: string; status: string }) {
  return (
    <div className="panel-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h3>{heading}</h3>
      </div>
      <span>{status}</span>
    </div>
  );
}

function DetailTerm({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function TagList({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="tag-list" aria-label={label}>
      <strong>{label}</strong>
      <div>
        {values.map((value) => (
          <span key={value}>{value}</span>
        ))}
      </div>
    </div>
  );
}
