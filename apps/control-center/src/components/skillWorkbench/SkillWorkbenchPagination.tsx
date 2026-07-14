import { NorthStarIcon } from "../NorthStarIcon";

export function Pagination({
  currentPage,
  pageCount,
  pageSize,
  pageStart,
  setPage,
  setPageSize,
  total,
}: {
  currentPage: number;
  pageCount: number;
  pageSize: number;
  pageStart: number;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  total: number;
}) {
  const visibleEnd = Math.min(total, pageStart + pageSize);
  return (
    <div className="skill-pagination" aria-label="Skill result pagination">
      <label>
        Rows per page:
        <select
          aria-label="Rows per page"
          onChange={(event) => setPageSize(Number(event.target.value))}
          value={pageSize}
        >
          <option value="10">10</option>
          <option value="25">25</option>
        </select>
      </label>
      <span>
        {total === 0 ? "0 of 0" : `${pageStart + 1}–${visibleEnd} of ${total}`}
      </span>
      <div className="skill-page-buttons">
        <button
          aria-label="Previous page"
          disabled={currentPage === 1}
          onClick={() => setPage(currentPage - 1)}
          type="button"
        >
          <NorthStarIcon name="chevron-left" size="sm" />
        </button>
        {Array.from({ length: pageCount }, (_, index) => index + 1).map(
          (pageNumber) => (
            <button
              aria-current={pageNumber === currentPage ? "page" : undefined}
              key={pageNumber}
              onClick={() => setPage(pageNumber)}
              type="button"
            >
              {pageNumber}
            </button>
          ),
        )}
        <button
          aria-label="Next page"
          disabled={currentPage === pageCount}
          onClick={() => setPage(currentPage + 1)}
          type="button"
        >
          <NorthStarIcon name="chevron-right" size="sm" />
        </button>
      </div>
    </div>
  );
}
