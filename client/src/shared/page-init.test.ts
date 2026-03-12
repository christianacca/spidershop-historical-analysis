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
import { initSortableTablePage, registerPageInit } from './page-init.js';

describe('initSortableTablePage', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    mountMock.mockReset();
    assertPayloadMock.mockReset();
    delete (window as Window & Record<string, unknown>)['breeder-tableData'];
  });

  it('mounts SortableTable with validated window rows and post-mount hook', () => {
    const rows = [{ Species: 'Aphonopelma seemanni' }];
    const postMount = vi.fn();
    document.body.innerHTML = '<div id="breeder-table-root"></div>';
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
    expect(postMount).toHaveBeenCalledTimes(1);
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