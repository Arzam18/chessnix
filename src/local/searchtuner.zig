//! Placeholder for the optional search-tuning command.
//!
//! The supplied Chessnix 1.5 WIP source archive imports this module from
//! src/main.zig, but does not include the implementation. The normal UCI
//! executable uses lib.program = .uci, so this module is never invoked by
//! the engine. Keep the missing import resolvable without changing UCI code.

pub fn run() !void {
    return error.SearchTunerSourceNotIncluded;
}
