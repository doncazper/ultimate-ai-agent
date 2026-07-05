import { useEffect, useMemo, useState } from "react";
import type {
  WorkBoardCardAuthorityState,
  WorkBoardCardPriority,
  WorkBoardCardReadModel,
  WorkBoardColumnReadModel,
  WorkBoardReadModel,
} from "../api/types";
import { SafeAlert } from "./SafeAlert";
import { NorthStarIcon } from "./NorthStarIcon";

type WorkBoardView = "board" | "list" | "proof";
type PriorityFilter = WorkBoardCardPriority | "all";
type AuthorityFilter = WorkBoardCardAuthorityState | "all";
type PreviewLayout = Record<string, string[]>;

interface WorkBoardPanelProps {
  board: WorkBoardReadModel;
  authoritative: boolean;
}

export function WorkBoardPanel({ authoritative, board }: WorkBoardPanelProps) {
  const backendOwned =
    authoritative &&
    board.backend_owned &&
    board.read_only &&
    board.safe_refs_only &&
    !board.non_authoritative_mock_fallback;
  const [activeView, setActiveView] = useState<WorkBoardView>("board");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("all");
  const [authorityFilter, setAuthorityFilter] = useState<AuthorityFilter>("all");
  const [query, setQuery] = useState("");
  const [draftCards, setDraftCards] = useState<WorkBoardCardReadModel[]>([]);
  const [layout, setLayout] = useState<PreviewLayout>(() =>
    initialLayout(board.columns),
  );
  const [selectedCardRef, setSelectedCardRef] = useState(
    board.cards[0]?.card_ref ?? "",
  );
  const [draggingCardRef, setDraggingCardRef] = useState<string | null>(null);
  const [notice, setNotice] = useState(board.drag_drop_posture.safe_summary);
  const [selectedBlockedLaneRef, setSelectedBlockedLaneRef] = useState(
    board.blocked_lanes[0]?.lane_ref ?? "",
  );

  useEffect(() => {
    setDraftCards([]);
    setLayout(initialLayout(board.columns));
    setSelectedCardRef(board.cards[0]?.card_ref ?? "");
    setNotice(board.drag_drop_posture.safe_summary);
    setSelectedBlockedLaneRef(board.blocked_lanes[0]?.lane_ref ?? "");
  }, [
    board.board_ref,
    board.blocked_lanes,
    board.cards,
    board.columns,
    board.drag_drop_posture.safe_summary,
  ]);

  const cards = useMemo(
    () => [...board.cards, ...draftCards],
    [board.cards, draftCards],
  );
  const cardsByRef = useMemo(
    () => new Map(cards.map((card) => [card.card_ref, card])),
    [cards],
  );
  const visibleCards = useMemo(
    () =>
      cards.filter((card) => {
        const text = `${card.title} ${card.safe_summary} ${card.tags.join(" ")}`.toLowerCase();
        const matchesQuery = text.includes(query.trim().toLowerCase());
        const matchesPriority =
          priorityFilter === "all" || card.priority === priorityFilter;
        const matchesAuthority =
          authorityFilter === "all" || card.authority_state === authorityFilter;
        return matchesQuery && matchesPriority && matchesAuthority;
      }),
    [authorityFilter, cards, priorityFilter, query],
  );
  const columnRefByCardRef = useMemo(() => {
    const next = new Map<string, string>();
    for (const column of board.columns) {
      for (const cardRef of layout[column.column_ref] ?? []) {
        next.set(cardRef, column.column_ref);
      }
    }
    for (const card of cards) {
      if (!next.has(card.card_ref)) {
        next.set(card.card_ref, card.column_ref);
      }
    }
    return next;
  }, [board.columns, cards, layout]);
  const visibleCardRefs = useMemo(
    () => new Set(visibleCards.map((card) => card.card_ref)),
    [visibleCards],
  );
  const boardStats = useMemo(
    () => ({
      blocked: cards.filter((card) => card.authority_state === "blocked").length,
      proposal: cards.filter((card) => card.authority_state === "proposal_only")
        .length,
      readOnly: cards.filter(
        (card) => card.authority_state === "enabled_read_only",
      ).length,
      total: cards.length,
      visible: visibleCards.length,
    }),
    [cards, visibleCards.length],
  );
  const selectedCard =
    cardsByRef.get(selectedCardRef) ?? visibleCards[0] ?? cards[0];
  const selectedBlockedLane =
    board.blocked_lanes.find(
      (lane) => lane.lane_ref === selectedBlockedLaneRef,
    ) ?? board.blocked_lanes[0];
  const previewChanged = hasPreviewChanged(board.columns, layout, draftCards);

  function moveCard(
    cardRef: string,
    targetColumnRef: string,
    beforeCardRef?: string,
  ) {
    if (cardRef === beforeCardRef) {
      return;
    }
    const card = cardsByRef.get(cardRef);
    const column = board.columns.find(
      (candidate) => candidate.column_ref === targetColumnRef,
    );
    if (!card || !column) {
      return;
    }
    setLayout((current) => {
      const next: PreviewLayout = {};
      for (const boardColumn of board.columns) {
        const refs = current[boardColumn.column_ref] ?? [];
        next[boardColumn.column_ref] = refs.filter((ref) => ref !== cardRef);
      }
      const targetRefs = [...(next[targetColumnRef] ?? [])];
      const targetIndex = beforeCardRef
        ? targetRefs.indexOf(beforeCardRef)
        : -1;
      if (targetIndex >= 0) {
        targetRefs.splice(targetIndex, 0, cardRef);
      } else {
        targetRefs.push(cardRef);
      }
      next[targetColumnRef] = targetRefs;
      return next;
    });
    setSelectedCardRef(cardRef);
    const beforeCard = beforeCardRef ? cardsByRef.get(beforeCardRef) : undefined;
    setNotice(
      beforeCard
        ? `${card.title} moved above ${beforeCard.title} in ${column.label} as an unsaved local layout preview.`
        : `${card.title} moved to ${column.label} as an unsaved local layout preview.`,
    );
  }

  function moveCardByOffset(cardRef: string, offset: number) {
    const currentColumnRef = columnRefByCardRef.get(cardRef);
    const currentIndex = board.columns.findIndex(
      (column) => column.column_ref === currentColumnRef,
    );
    if (currentIndex < 0) {
      return;
    }
    const targetIndex = Math.min(
      Math.max(currentIndex + offset, 0),
      board.columns.length - 1,
    );
    if (targetIndex === currentIndex) {
      const card = cardsByRef.get(cardRef);
      if (card) {
        setSelectedCardRef(cardRef);
        setNotice(
          `${card.title} is already at the ${offset < 0 ? "first" : "last"} lane.`,
        );
      }
      return;
    }
    moveCard(cardRef, board.columns[targetIndex].column_ref);
  }

  function canMoveCardByOffset(cardRef: string, offset: number) {
    const currentColumnRef = columnRefByCardRef.get(cardRef);
    const currentIndex = board.columns.findIndex(
      (column) => column.column_ref === currentColumnRef,
    );
    if (currentIndex < 0) {
      return false;
    }
    const targetIndex = Math.min(
      Math.max(currentIndex + offset, 0),
      board.columns.length - 1,
    );
    return targetIndex !== currentIndex;
  }

  function resetPreview() {
    setDraftCards([]);
    setLayout(initialLayout(board.columns));
    setSelectedCardRef(board.cards[0]?.card_ref ?? "");
    setNotice("Local layout preview reset to the backend-owned board order.");
  }

  function addLocalDraft() {
    const draftNumber = draftCards.length + 1;
    const triageColumnRef = board.columns[0]?.column_ref ?? "work-board-column:triage";
    const draft: WorkBoardCardReadModel = {
      card_ref: `work-board-card:local-preview-draft-${draftNumber}`,
      title: `Local draft ${draftNumber}`,
      safe_summary:
        "Ephemeral UI-only draft for shaping a possible board item. It is not persisted and creates no backend task.",
      column_ref: triageColumnRef,
      priority: "medium",
      authority_state: "proposal_only",
      owner_ref: "owner-ref:control-center-local-preview",
      progress_label: "Preview only",
      proof_refs: ["proof-ref:work-board-local-preview"],
      evidence_refs: ["evidence-ref:work-board-local-preview"],
      blocker_refs: ["blocked-state:work-board-no-board-mutation"],
      surface_refs: [board.route_ref],
      cli_inspection_refs: board.cli_inspection_refs,
      tags: ["local-preview", "draft"],
      raw_path_included: false,
      raw_content_included: false,
      mutation_enabled: false,
      drag_persistence_enabled: false,
    };
    setDraftCards((current) => [...current, draft]);
    setLayout((current) => ({
      ...current,
      [triageColumnRef]: [...(current[triageColumnRef] ?? []), draft.card_ref],
    }));
    setSelectedCardRef(draft.card_ref);
    setNotice("Local draft added as UI-only preview. It is not backend truth.");
  }

  function openBlockedLane(laneRef?: string) {
    if (laneRef) {
      setSelectedBlockedLaneRef(laneRef);
    }
    setActiveView("proof");
    setNotice("Durable Work Board mutation remains blocked pending a governed lane.");
  }

  function inspectCard(cardRef: string) {
    const card = cardsByRef.get(cardRef);
    setSelectedCardRef(cardRef);
    setActiveView("proof");
    setNotice(
      card
        ? `${card.title} opened in Proof view with safe refs only.`
        : "Selected Work Board card opened in Proof view with safe refs only.",
    );
  }

  return (
    <section
      className="page-section work-board"
      aria-labelledby="work-board-heading"
      data-testid="work-board"
    >
      <div className="section-heading work-board-heading">
        <div>
          <p className="eyebrow">Local-first operator kanban</p>
          <h2 id="work-board-heading">{board.title}</h2>
        </div>
        <span className="status-pill compact">
          {backendOwned ? board.status.replaceAll("_", " ") : "non-authoritative mock fallback"}
        </span>
      </div>

      <SafeAlert
        tone={backendOwned ? "info" : "warning"}
        title={
          backendOwned
            ? "Backend-owned Work Board"
            : "Non-authoritative Work Board fallback"
        }
        message={
          backendOwned
            ? "Python Core owns the board order and safe refs. Drag/drop changes here are preview-only until a mutation lane exists."
            : "This Work Board is mock fallback for visual continuity only; it is not durable workflow truth."
        }
      />

      <WorkBoardStatusGrid
        backendOwned={backendOwned}
        blockedCount={boardStats.blocked}
        previewChanged={previewChanged}
        proposalCount={boardStats.proposal}
        readOnlyCount={boardStats.readOnly}
        totalCount={boardStats.total}
        visibleCount={boardStats.visible}
      />

      <div className="work-board-chrome" aria-label="Work Board controls">
        <div className="work-board-ref-strip">
          <RefChip label="Board" value={board.board_ref} />
          <RefChip label="Route" value={board.backend_route_refs[0]} />
          <RefChip label="CLI" value={board.cli_inspection_refs[0]} />
        </div>
        <div className="work-board-controls">
          <div className="work-board-search-shell">
            <label className="work-board-search">
              <NorthStarIcon name="search" />
              <span className="sr-only">Search Work Board</span>
              <input
                aria-label="Search Work Board"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search board"
                value={query}
              />
            </label>
            {query ? (
              <button
                aria-label="Clear Work Board search"
                className="work-board-search-clear"
                onClick={() => setQuery("")}
                type="button"
              >
                <NorthStarIcon name="x" />
              </button>
            ) : null}
          </div>
          <SegmentedControl
            label="Work Board view"
            onChange={setActiveView}
            options={[
              ["board", "Board"],
              ["list", "List"],
              ["proof", "Proof"],
            ]}
            value={activeView}
          />
          <button className="icon-text-button" onClick={addLocalDraft} type="button">
            <NorthStarIcon name="edit" />
            Add local draft
          </button>
          <button className="icon-text-button" onClick={resetPreview} type="button">
            <NorthStarIcon name="archive" />
            Reset preview
          </button>
          <button
            className="icon-text-button warning"
            onClick={() => openBlockedLane()}
            type="button"
          >
            <NorthStarIcon name="lock" />
            Request persistence lane
          </button>
        </div>
      </div>

      <div className="work-board-filter-row" aria-label="Work Board filters">
        <FilterGroup
          label="Priority"
          onChange={setPriorityFilter}
          options={[
            ["all", "All"],
            ["critical", "Critical"],
            ["high", "High"],
            ["medium", "Medium"],
            ["low", "Low"],
          ]}
          value={priorityFilter}
        />
        <FilterGroup
          label="Authority"
          onChange={setAuthorityFilter}
          options={[
            ["all", "All"],
            ["enabled_read_only", "Read-only"],
            ["proposal_only", "Proposal"],
            ["blocked", "Blocked"],
          ]}
          value={authorityFilter}
        />
        <span className={`work-board-preview-state ${previewChanged ? "changed" : ""}`}>
          {previewChanged ? "Unsaved local preview" : "Backend order"}
        </span>
      </div>

      <div className="work-board-notice" role="status">
        <NorthStarIcon name={previewChanged ? "info" : "shield-check"} />
        <span>{notice}</span>
      </div>

      {activeView === "board" ? (
        <div className="work-board-layout">
          <div className="work-board-columns" aria-label="Kanban columns">
            {board.columns.map((column) => (
              <WorkBoardColumn
                cardsByRef={cardsByRef}
                canMoveCardByOffset={canMoveCardByOffset}
                column={column}
                draggingCardRef={draggingCardRef}
                key={column.column_ref}
                layout={layout}
                moveCard={moveCard}
                moveCardByOffset={moveCardByOffset}
                openBlockedLane={openBlockedLane}
                selectedCardRef={selectedCard?.card_ref}
                setDraggingCardRef={setDraggingCardRef}
                setSelectedCardRef={setSelectedCardRef}
                visibleCardRefs={visibleCardRefs}
              />
            ))}
          </div>
          <WorkBoardInspector
            authoritative={authoritative}
            backendOwned={backendOwned}
            board={board}
            card={selectedCard}
            openBlockedLane={openBlockedLane}
            selectedBlockedLane={selectedBlockedLane}
          />
        </div>
      ) : activeView === "list" ? (
        <WorkBoardList
          canMoveCardByOffset={canMoveCardByOffset}
          cards={visibleCards}
          columnRefByCardRef={columnRefByCardRef}
          columns={board.columns}
          inspectCard={inspectCard}
          moveCardByOffset={moveCardByOffset}
        />
      ) : (
        <WorkBoardProof
          board={board}
          card={selectedCard}
          openBlockedLane={openBlockedLane}
          selectedBlockedLane={selectedBlockedLane}
        />
      )}
    </section>
  );
}

function WorkBoardColumn({
  cardsByRef,
  canMoveCardByOffset,
  column,
  draggingCardRef,
  layout,
  moveCard,
  moveCardByOffset,
  openBlockedLane,
  selectedCardRef,
  setDraggingCardRef,
  setSelectedCardRef,
  visibleCardRefs,
}: {
  cardsByRef: Map<string, WorkBoardCardReadModel>;
  canMoveCardByOffset: (cardRef: string, offset: number) => boolean;
  column: WorkBoardColumnReadModel;
  draggingCardRef: string | null;
  layout: PreviewLayout;
  moveCard: (
    cardRef: string,
    targetColumnRef: string,
    beforeCardRef?: string,
  ) => void;
  moveCardByOffset: (cardRef: string, offset: number) => void;
  openBlockedLane: (laneRef?: string) => void;
  selectedCardRef?: string;
  setDraggingCardRef: (cardRef: string | null) => void;
  setSelectedCardRef: (cardRef: string) => void;
  visibleCardRefs: Set<string>;
}) {
  const cardRefs = (layout[column.column_ref] ?? []).filter((cardRef) =>
    visibleCardRefs.has(cardRef),
  );
  return (
    <section
      aria-label={`${column.label} column`}
      className={`work-board-column ${draggingCardRef ? "drop-ready" : ""}`}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        const cardRef = event.dataTransfer.getData("text/plain") || draggingCardRef;
        if (cardRef) {
          moveCard(cardRef, column.column_ref);
        }
        setDraggingCardRef(null);
      }}
    >
      <div className="work-board-column-header">
        <div>
          <span>{column.label}</span>
          <small>{column.safe_summary}</small>
        </div>
        <strong>{cardRefs.length}/{column.wip_limit}</strong>
      </div>
      <div className="work-board-card-stack">
        {cardRefs.map((cardRef) => {
          const card = cardsByRef.get(cardRef);
          if (!card) {
            return null;
          }
          return (
            <WorkBoardCard
              card={card}
              canMoveCardByOffset={canMoveCardByOffset}
              columnRef={column.column_ref}
              draggingCardRef={draggingCardRef}
              isSelected={selectedCardRef === card.card_ref}
              key={card.card_ref}
              moveCard={moveCard}
              moveCardByOffset={moveCardByOffset}
              openBlockedLane={openBlockedLane}
              setDraggingCardRef={setDraggingCardRef}
              setSelectedCardRef={setSelectedCardRef}
            />
          );
        })}
        {cardRefs.length === 0 ? (
          <div className="work-board-empty-column">No matching cards</div>
        ) : null}
      </div>
    </section>
  );
}

function WorkBoardCard({
  card,
  canMoveCardByOffset,
  columnRef,
  draggingCardRef,
  isSelected,
  moveCard,
  moveCardByOffset,
  openBlockedLane,
  setDraggingCardRef,
  setSelectedCardRef,
}: {
  card: WorkBoardCardReadModel;
  canMoveCardByOffset: (cardRef: string, offset: number) => boolean;
  columnRef: string;
  draggingCardRef: string | null;
  isSelected: boolean;
  moveCard: (
    cardRef: string,
    targetColumnRef: string,
    beforeCardRef?: string,
  ) => void;
  moveCardByOffset: (cardRef: string, offset: number) => void;
  openBlockedLane: (laneRef?: string) => void;
  setDraggingCardRef: (cardRef: string | null) => void;
  setSelectedCardRef: (cardRef: string) => void;
}) {
  return (
    <article
      aria-label={`${card.title} card`}
      className={`work-board-card ${isSelected ? "selected" : ""} ${
        draggingCardRef && draggingCardRef !== card.card_ref ? "drop-target" : ""
      }`}
      draggable
      onClick={() => setSelectedCardRef(card.card_ref)}
      onDragEnd={() => setDraggingCardRef(null)}
      onDragOver={(event) => {
        if (draggingCardRef && draggingCardRef !== card.card_ref) {
          event.preventDefault();
        }
      }}
      onDragStart={(event) => {
        event.dataTransfer.setData("text/plain", card.card_ref);
        event.dataTransfer.effectAllowed = "move";
        setDraggingCardRef(card.card_ref);
      }}
      onDrop={(event) => {
        event.preventDefault();
        event.stopPropagation();
        const cardRef = event.dataTransfer.getData("text/plain") || draggingCardRef;
        if (cardRef && cardRef !== card.card_ref) {
          moveCard(cardRef, columnRef, card.card_ref);
        }
        setDraggingCardRef(null);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          setSelectedCardRef(card.card_ref);
        }
        if (event.key === "ArrowLeft") {
          event.preventDefault();
          moveCardByOffset(card.card_ref, -1);
        }
        if (event.key === "ArrowRight") {
          event.preventDefault();
          moveCardByOffset(card.card_ref, 1);
        }
      }}
      tabIndex={0}
    >
      <div className="work-board-card-topline">
        <span className="work-board-card-handle" aria-hidden="true">
          ::
        </span>
        <span className={`priority-dot ${card.priority}`} />
        <span className="work-board-card-progress">{card.progress_label}</span>
        <span className={`authority-mini ${card.authority_state}`}>
          {card.authority_state.replaceAll("_", " ")}
        </span>
      </div>
      <h3>{card.title}</h3>
      <p>{card.safe_summary}</p>
      <div className="work-board-card-tags">
        {card.tags.map((tag) => (
          <span key={tag}>{tag}</span>
        ))}
      </div>
      <div className="work-board-card-actions" aria-label={`${card.title} actions`}>
        <button
          aria-label={`Move ${card.title} left`}
          onClick={(event) => {
            event.stopPropagation();
            moveCardByOffset(card.card_ref, -1);
          }}
          disabled={!canMoveCardByOffset(card.card_ref, -1)}
          type="button"
        >
          <NorthStarIcon name="chevron-left" />
        </button>
        <button
          aria-label={`Move ${card.title} right`}
          onClick={(event) => {
            event.stopPropagation();
            moveCardByOffset(card.card_ref, 1);
          }}
          disabled={!canMoveCardByOffset(card.card_ref, 1)}
          type="button"
        >
          <NorthStarIcon name="chevron-right" />
        </button>
        <button
          onClick={(event) => {
            event.stopPropagation();
            setSelectedCardRef(card.card_ref);
          }}
          type="button"
        >
          <NorthStarIcon name="eye" />
          Select
        </button>
        <button
          onClick={(event) => {
            event.stopPropagation();
            openBlockedLane();
          }}
          type="button"
        >
          <NorthStarIcon name="lock" />
          Persist blocked
        </button>
      </div>
    </article>
  );
}

function WorkBoardInspector({
  authoritative,
  backendOwned,
  board,
  card,
  openBlockedLane,
  selectedBlockedLane,
}: {
  authoritative: boolean;
  backendOwned: boolean;
  board: WorkBoardReadModel;
  card?: WorkBoardCardReadModel;
  openBlockedLane: (laneRef?: string) => void;
  selectedBlockedLane?: WorkBoardReadModel["blocked_lanes"][number];
}) {
  return (
    <aside className="work-board-inspector" aria-label="Work Board inspector">
      <div className="inspector-card">
        <p className="eyebrow">Selection</p>
        <h3>{card?.title ?? "No card selected"}</h3>
        <p>{card?.safe_summary ?? board.safe_summary}</p>
        <div className="inspector-ref-list">
          {(card?.proof_refs ?? board.proof_refs).map((ref) => (
            <span key={ref}>{ref}</span>
          ))}
        </div>
      </div>
      <div className="inspector-card">
        <p className="eyebrow">Authority</p>
        <h3>{backendOwned ? "Read-only backend truth" : "Fallback only"}</h3>
        <p>
          {authoritative
            ? board.repo_safe_scope
            : "Connection is degraded or fallback. Controls remain local preview only."}
        </p>
        <button onClick={() => openBlockedLane()} type="button">
          <NorthStarIcon name="lock" />
          Show blocked lane
        </button>
      </div>
      {selectedBlockedLane ? (
        <div className="inspector-card blocked">
          <p className="eyebrow">Blocked lane</p>
          <h3>{selectedBlockedLane.label}</h3>
          <p>{selectedBlockedLane.safe_summary}</p>
          <div className="inspector-ref-list">
            {selectedBlockedLane.blocked_authority_refs.map((ref) => (
              <span key={ref}>{ref}</span>
            ))}
          </div>
        </div>
      ) : null}
    </aside>
  );
}

function WorkBoardList({
  canMoveCardByOffset,
  cards,
  columnRefByCardRef,
  columns,
  inspectCard,
  moveCardByOffset,
}: {
  canMoveCardByOffset: (cardRef: string, offset: number) => boolean;
  cards: WorkBoardCardReadModel[];
  columnRefByCardRef: Map<string, string>;
  columns: WorkBoardColumnReadModel[];
  inspectCard: (cardRef: string) => void;
  moveCardByOffset: (cardRef: string, offset: number) => void;
}) {
  const columnByRef = new Map(columns.map((column) => [column.column_ref, column]));
  if (cards.length === 0) {
    return (
      <div className="work-board-list" aria-label="Work Board list view">
        <div className="work-board-empty-list">No cards match current filters</div>
      </div>
    );
  }
  return (
    <div className="work-board-list" aria-label="Work Board list view">
      {cards.map((card) => (
        <article
          aria-label={`${card.title} list row`}
          className="work-board-list-row"
          key={card.card_ref}
        >
          <div>
            <strong>{card.title}</strong>
            <span>
              {columnByRef.get(
                columnRefByCardRef.get(card.card_ref) ?? card.column_ref,
              )?.label ?? "Preview"}
            </span>
          </div>
          <p>{card.safe_summary}</p>
          <span>{card.priority}</span>
          <span>{card.authority_state.replaceAll("_", " ")}</span>
          <button onClick={() => inspectCard(card.card_ref)} type="button">
            <NorthStarIcon name="eye" />
            Inspect
          </button>
          <button
            disabled={!canMoveCardByOffset(card.card_ref, -1)}
            onClick={() => moveCardByOffset(card.card_ref, -1)}
            type="button"
          >
            <NorthStarIcon name="chevron-left" />
            Move left
          </button>
          <button
            disabled={!canMoveCardByOffset(card.card_ref, 1)}
            onClick={() => moveCardByOffset(card.card_ref, 1)}
            type="button"
          >
            <NorthStarIcon name="chevron-right" />
            Move right
          </button>
        </article>
      ))}
    </div>
  );
}

function WorkBoardProof({
  board,
  card,
  openBlockedLane,
  selectedBlockedLane,
}: {
  board: WorkBoardReadModel;
  card?: WorkBoardCardReadModel;
  openBlockedLane: (laneRef?: string) => void;
  selectedBlockedLane?: WorkBoardReadModel["blocked_lanes"][number];
}) {
  return (
    <div className="work-board-proof-grid" aria-label="Work Board proof view">
      <div className="inspector-card">
        <p className="eyebrow">Board proof</p>
        <h3>{board.contract_ref}</h3>
        <p>{board.full_strength_goal}</p>
        <div className="inspector-ref-list">
          {board.proof_refs.concat(board.evidence_refs).map((ref) => (
            <span key={ref}>{ref}</span>
          ))}
        </div>
      </div>
      <div className="inspector-card">
        <p className="eyebrow">Selected card</p>
        <h3>{card?.title ?? "No selected card"}</h3>
        <p>{card?.safe_summary ?? "Select a card to inspect its safe refs."}</p>
        <div className="inspector-ref-list">
          {(card?.surface_refs ?? board.frontend_route_refs).map((ref) => (
            <span key={ref}>{ref}</span>
          ))}
        </div>
      </div>
      <div className="inspector-card blocked">
        <p className="eyebrow">Promotion lane</p>
        <h3>{selectedBlockedLane?.label ?? "Durable board edits"}</h3>
        <p>{selectedBlockedLane?.safe_summary ?? board.next_safe_action}</p>
        <div className="inspector-ref-list">
          {(selectedBlockedLane?.blocked_authority_refs ??
            board.blocked_authority_refs
          ).map((ref) => (
            <span key={ref}>{ref}</span>
          ))}
        </div>
        <button onClick={() => openBlockedLane()} type="button">
          <NorthStarIcon name="lock" />
          Keep blocked visible
        </button>
      </div>
    </div>
  );
}

function WorkBoardStatusGrid({
  backendOwned,
  blockedCount,
  previewChanged,
  proposalCount,
  readOnlyCount,
  totalCount,
  visibleCount,
}: {
  backendOwned: boolean;
  blockedCount: number;
  previewChanged: boolean;
  proposalCount: number;
  readOnlyCount: number;
  totalCount: number;
  visibleCount: number;
}) {
  return (
    <div className="north-star-status-grid work-board-status-grid">
      <WorkBoardStatusTile
        detail={backendOwned ? "backend current" : "fallback only"}
        label="Board Truth"
        tone={backendOwned ? "green" : "orange"}
        value={backendOwned ? "Live" : "Mock"}
      />
      <WorkBoardStatusTile
        detail={`${totalCount} total`}
        label="Visible Cards"
        tone={visibleCount > 0 ? "green" : "gray"}
        value={String(visibleCount)}
      />
      <WorkBoardStatusTile
        detail="safe read model"
        label="Read-only"
        tone="green"
        value={String(readOnlyCount)}
      />
      <WorkBoardStatusTile
        detail="local review"
        label="Proposal"
        tone={proposalCount > 0 ? "orange" : "gray"}
        value={String(proposalCount)}
      />
      <WorkBoardStatusTile
        detail="needs authority"
        label="Blocked"
        tone={blockedCount > 0 ? "red" : "green"}
        value={String(blockedCount)}
      />
      <WorkBoardStatusTile
        detail={previewChanged ? "local only" : "backend order"}
        label="Layout"
        tone={previewChanged ? "orange" : "green"}
        value={previewChanged ? "Preview" : "Order"}
      />
    </div>
  );
}

function WorkBoardStatusTile({
  detail,
  label,
  tone,
  value,
}: {
  detail: string;
  label: string;
  tone: "green" | "gray" | "orange" | "red";
  value: string;
}) {
  return (
    <article className={`north-star-status-tile ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function SegmentedControl<T extends string>({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (value: T) => void;
  options: [T, string][];
  value: T;
}) {
  return (
    <div className="segmented-control" aria-label={label}>
      {options.map(([optionValue, optionLabel]) => (
        <button
          aria-pressed={value === optionValue}
          className={value === optionValue ? "active" : ""}
          key={optionValue}
          onClick={() => onChange(optionValue)}
          type="button"
        >
          {optionLabel}
        </button>
      ))}
    </div>
  );
}

function FilterGroup<T extends string>({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (value: T) => void;
  options: [T, string][];
  value: T;
}) {
  return (
    <div className="filter-group" aria-label={`${label} filter`}>
      <span>{label}</span>
      {options.map(([optionValue, optionLabel]) => (
        <button
          aria-pressed={value === optionValue}
          className={value === optionValue ? "active" : ""}
          key={optionValue}
          onClick={() => onChange(optionValue)}
          type="button"
        >
          {optionLabel}
        </button>
      ))}
    </div>
  );
}

function RefChip({ label, value }: { label: string; value?: string }) {
  return (
    <span className="work-board-ref-chip">
      <small>{label}</small>
      <strong>{value ?? "unavailable"}</strong>
    </span>
  );
}

function initialLayout(columns: WorkBoardColumnReadModel[]): PreviewLayout {
  return Object.fromEntries(
    columns.map((column) => [column.column_ref, [...column.card_refs]]),
  );
}

function hasPreviewChanged(
  columns: WorkBoardColumnReadModel[],
  layout: PreviewLayout,
  draftCards: WorkBoardCardReadModel[],
): boolean {
  if (draftCards.length > 0) {
    return true;
  }
  return columns.some((column) => {
    const current = layout[column.column_ref] ?? [];
    return current.join("|") !== column.card_refs.join("|");
  });
}
