import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mountMock, assertPayloadMock } = vi.hoisted(() => ({
  mountMock: vi.fn(),
  assertPayloadMock: vi.fn(),
}));

vi.mock('svelte', () => ({
  mount: mountMock,
}));

vi.mock('./payload-validation.js', () => ({
  assertPayload: assertPayloadMock,
}));

vi.mock('./components/SortableTable.svelte', () => ({
  default: { name: 'SortableTableMock' },
}));

import SortableTable from './components/SortableTable.svelte';
import { completeTableMount, initSortableTablePage, registerPageInit } from './page-init.js';

describe('initSortableTablePage', () => {
  let performanceNowSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    document.body.innerHTML = '';
    mountMock.mockReset();
    assertPayloadMock.mockReset();
    vi.useFakeTimers();
    performanceNowSpy = vi.spyOn(performance, 'now').mockReturnValue(40);
    delete (window as Window & Record<string, unknown>)['breeder-tableData'];
  });

  afterEach(() => {
    performanceNowSpy.mockRestore();
    vi.useRealTimers();
  });

  it('mounts SortableTable with validated window rows and post-mount hook', () => {
    const rows = [{ Species: 'Aphonopelma seemanni' }];
    const postMount = vi.fn();
    document.body.innerHTML = `
      <div data-table-shell="breeder-table" data-table-ready="false">
        <div data-table-skeleton-for="breeder-table"></div>
        <div id="breeder-table-root"></div>
      </div>
    `;
    (window as Window & Record<string, unknown>)['breeder-tableData'] = rows;

    initSortableTablePage({
      tableId: 'breeder-table',
      columns: [{ key: 'Species', label: 'Species' }],
      filterConfig: { showSearch: true, statsLabel: 'species' },
      primaryToggle: true,
      postMount,
    });

    expect(assertPayloadMock).toHaveBeenCalledWith('breeder-table', rows);
    expect(mountMock).toHaveBeenCalledWith(SortableTable, {
      target: document.getElementById('breeder-table-root'),
      props: {
        tableId: 'breeder-table',
        rows,
        columns: [{ key: 'Species', label: 'Species' }],
        filterConfig: { showSearch: true, statsLabel: 'species' },
        primaryToggle: true,
      },
    });
    expect(document.querySelector('[data-table-skeleton-for="breeder-table"]')).not.toBeNull();
    expect(document.querySelector('[data-table-shell="breeder-table"]')).toHaveAttribute(
      'data-table-ready',
      'false',
    );
    vi.advanceTimersByTime(479);
    expect(document.querySelector('[data-table-shell="breeder-table"]')).toHaveAttribute(
      'data-table-ready',
      'false',
    );
    vi.advanceTimersByTime(1);
    expect(document.querySelector('[data-table-shell="breeder-table"]')).toHaveAttribute(
      'data-table-ready',
      'true',
    );
    vi.advanceTimersByTime(259);
    expect(document.querySelector('[data-table-skeleton-for="breeder-table"]')).not.toBeNull();
    vi.advanceTimersByTime(1);
    expect(document.querySelector('[data-table-skeleton-for="breeder-table"]')).toBeNull();
    expect(postMount).toHaveBeenCalledTimes(1);
  });

  it('leaves pages without a server skeleton alone while still mounting successfully', () => {
    const rows = [{ Species: 'Brachypelma hamorii' }];
    document.body.innerHTML = '<div id="breeder-table-root"></div>';
    (window as Window & Record<string, unknown>)['breeder-tableData'] = rows;

    initSortableTablePage({
      tableId: 'breeder-table',
      columns: [{ key: 'Species', label: 'Species' }],
      filterConfig: { showSearch: true, statsLabel: 'species' },
    });

    expect(mountMock).toHaveBeenCalledTimes(1);
    expect(document.querySelector('[data-table-skeleton-for="breeder-table"]')).toBeNull();
  });

  it('returns early when the mount target is missing', () => {
    const postMount = vi.fn();

    initSortableTablePage({
      tableId: 'breeder-table',
      columns: [{ key: 'Species', label: 'Species' }],
      filterConfig: { showSearch: true, statsLabel: 'species' },
      postMount,
    });

    expect(assertPayloadMock).not.toHaveBeenCalled();
    expect(mountMock).not.toHaveBeenCalled();
    expect(postMount).not.toHaveBeenCalled();
  });
});

describe('completeTableMount', () => {
  let performanceNowSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    document.body.innerHTML = '';
    vi.useFakeTimers();
    performanceNowSpy = vi.spyOn(performance, 'now').mockReturnValue(40);
  });

  afterEach(() => {
    performanceNowSpy.mockRestore();
    vi.useRealTimers();
  });

  it('waits for the minimum skeleton dwell, then removes the skeleton after the fade delay', () => {
    document.body.innerHTML = `
      <div data-table-shell="history-table" data-table-ready="false">
        <div data-table-skeleton-for="history-table"></div>
      </div>
    `;

    completeTableMount('history-table');

    expect(document.querySelector('[data-table-shell="history-table"]')).toHaveAttribute(
      'data-table-ready',
      'false',
    );
    expect(document.querySelector('[data-table-skeleton-for="history-table"]')).not.toBeNull();

    vi.advanceTimersByTime(479);
    expect(document.querySelector('[data-table-shell="history-table"]')).toHaveAttribute(
      'data-table-ready',
      'false',
    );
    vi.advanceTimersByTime(1);
    expect(document.querySelector('[data-table-shell="history-table"]')).toHaveAttribute(
      'data-table-ready',
      'true',
    );

    vi.advanceTimersByTime(259);
    expect(document.querySelector('[data-table-skeleton-for="history-table"]')).not.toBeNull();

    vi.advanceTimersByTime(1);
    expect(document.querySelector('[data-table-skeleton-for="history-table"]')).toBeNull();
  });

  it('starts the cross-fade immediately when the skeleton has already been visible long enough', () => {
    performanceNowSpy.mockReturnValue(600);
    document.body.innerHTML = `
      <div data-table-shell="snapshot-table" data-table-ready="false">
        <div data-table-skeleton-for="snapshot-table"></div>
      </div>
    `;

    completeTableMount('snapshot-table');

    expect(document.querySelector('[data-table-shell="snapshot-table"]')).toHaveAttribute(
      'data-table-ready',
      'true',
    );
    vi.advanceTimersByTime(259);
    expect(document.querySelector('[data-table-skeleton-for="snapshot-table"]')).not.toBeNull();
    vi.advanceTimersByTime(1);
    expect(document.querySelector('[data-table-skeleton-for="snapshot-table"]')).toBeNull();
  });
});

describe('registerPageInit', () => {
  beforeEach(() => {
    delete (document as Document & { readyState?: DocumentReadyState }).readyState;
  });

  it('calls init immediately when the document is already ready', () => {
    const init = vi.fn();

    registerPageInit(init);

    expect(init).toHaveBeenCalledTimes(1);
  });

  it('registers a DOMContentLoaded listener when the document is still loading', () => {
    Object.defineProperty(document, 'readyState', {
      configurable: true,
      get: () => 'loading',
    });
    const init = vi.fn();
    const addEventListenerSpy = vi.spyOn(document, 'addEventListener');

    registerPageInit(init);

    expect(init).not.toHaveBeenCalled();
    expect(addEventListenerSpy).toHaveBeenCalledWith('DOMContentLoaded', init);
  });
});