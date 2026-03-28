import { describe, expect, it, vi } from 'vitest';

const { registerPageInitMock, registerSortableTablePageMock } = vi.hoisted(() => ({
  registerPageInitMock: vi.fn(),
  registerSortableTablePageMock: vi.fn(),
}));

vi.mock('./page-init.js', () => ({
  registerPageInit: registerPageInitMock,
  registerSortableTablePage: registerSortableTablePageMock,
}));

import { bootstrapSortableTablePage } from './page-entry.js';

describe('bootstrapSortableTablePage', () => {
  it('registers the sortable table page config directly when no pre-init hook is supplied', () => {
    const config = { tableId: 'snapshot-table', columns: [] };

    bootstrapSortableTablePage(config);

    expect(registerPageInitMock).not.toHaveBeenCalled();
    expect(registerSortableTablePageMock).toHaveBeenCalledWith(config);
  });

  it('registers an optional pre-init hook before wiring the sortable table page', () => {
    const config = { tableId: 'breeder-table', columns: [] };
    const beforeTableInit = vi.fn();

    bootstrapSortableTablePage(config, { beforeTableInit });

    expect(registerPageInitMock).toHaveBeenCalledTimes(1);
    const registeredInit = registerPageInitMock.mock.calls[0][0] as () => void;
    registeredInit();
    expect(beforeTableInit).toHaveBeenCalledTimes(1);
    expect(registerSortableTablePageMock).toHaveBeenCalledWith(config);
  });
});