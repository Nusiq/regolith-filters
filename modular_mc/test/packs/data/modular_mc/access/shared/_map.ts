import _resource_map from "../../_shared/_resource_map.ts";
const { sharedBehavior } = _resource_map;

export const MAP = [
    {
        source: sharedBehavior,
        target: ":autoFlat"
    },
    {
        source: sharedBehavior,
        target: {
            path: ":autoFlat",
            subpath: "subpath",
            name: ":auto"
        }
    }
]