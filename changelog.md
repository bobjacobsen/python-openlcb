All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [Unreleased] - 2026-09-14

### Changed
- Rename `DatagramWriteMemo` to **`DatagramSendMemo`** and `DatagramReadMemo` to **`DatagramReceiveMemo`** to distinguish meaning of read/write from the higher network layers (For example, in "DatagramWriteMemo" "Write" had two different meanings--one for port flow direction, one for request type, as it could be associated with a MemoryReadMemo. Now a MemoryReadMemo is associated with a "DatagramSendMemo" denoting it was requested by us but we may be still requesting a read such as in that case).
