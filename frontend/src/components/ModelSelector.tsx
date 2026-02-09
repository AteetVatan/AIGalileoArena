import { AVAILABLE_MODELS } from "@/lib/constants";
import { AlertTriangle, CheckCircle, Info, RefreshCw, XCircle } from "lucide-react";
import type { KeyValidationResult, KeyValidationStatus } from "@/lib/types";
import { RefObject } from "react";

interface Props {
    selectedModel: string;
    onSelectModel: (model: string) => void;
    isModelDisabled: (model: (typeof AVAILABLE_MODELS)[0]) => boolean;
    getValidationStatus: (model: (typeof AVAILABLE_MODELS)[0]) => KeyValidationStatus | null;
    validationLoading: boolean;
    onRefreshValidation: () => void;
    keyValidation: Map<string, KeyValidationResult>;
    highlighted?: boolean;
    containerRef?: RefObject<HTMLDivElement>;
}

export function ModelSelector({
    selectedModel,
    onSelectModel,
    isModelDisabled,
    getValidationStatus,
    validationLoading,
    onRefreshValidation,
    keyValidation,
    highlighted,
    containerRef
}: Props) {

    return (
        <div
            ref={containerRef}
            className={`glass-panel border-white/10 bg-slate-950/40 backdrop-blur-md rounded-3xl p-6 shadow-2xl transition-all duration-700 ${highlighted
                ? 'border-cyan-400/60 bg-cyan-500/10 shadow-[0_0_30px_rgba(34,211,238,0.4)] ring-2 ring-cyan-400/30'
                : ''
                }`}
        >
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xs font-semibold text-cyan-400 tracking-widest uppercase flex items-center gap-2">
                    Inference Engine
                    <div className="relative group/info">
                        <Info className="w-3 h-3 text-white/30 cursor-help" />
                        <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-48 p-2 bg-black/90 border border-white/10 rounded-lg text-[10px] text-white/70 pointer-events-none opacity-0 group-hover/info:opacity-100 transition-opacity z-50">
                            Select the LLM that will power the debate agents.
                        </div>
                    </div>
                </h2>

                <button
                    onClick={onRefreshValidation}
                    disabled={validationLoading}
                    className="p-1.5 rounded-lg hover:bg-white/5 text-white/40 hover:text-cyan-400 transition-colors disabled:opacity-50"
                    title="Refresh API key validation"
                >
                    <RefreshCw className={`w-3 h-3 ${validationLoading ? "animate-spin" : ""}`} />
                </button>
            </div>

            <div className="relative">
                <select
                    value={selectedModel}
                    onChange={(e) => onSelectModel(e.target.value)}
                    className="w-full appearance-none bg-background/50 border border-primary/20 rounded-xl px-5 py-4 text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all font-medium"
                >
                    <option value="" className="bg-background text-muted-foreground">-- Select an Inference Engine --</option>
                    {AVAILABLE_MODELS.map((model) => {
                        const isDisabled = isModelDisabled(model);
                        // We can't render complex icons inside <option>, so we stick to text.
                        // We could show status in text if needed, e.g. " (Offline)"
                        return (
                            <option
                                key={model.id}
                                value={model.id}
                                disabled={isDisabled}
                                className="bg-background text-foreground"
                            >
                                {model.label} ({model.provider})
                            </option>
                        );
                    })}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground">▼</div>
            </div>

            {/* Optional: Show selected model status below the dropdown if needed */}
            {selectedModel && (() => {
                const model = AVAILABLE_MODELS.find(m => m.id === selectedModel);
                if (!model) return null;
                const status = getValidationStatus(model);
                if (status && status !== "VALID") {
                    const result = keyValidation.get(model.api_key_env);
                    let errorText = result?.error_message || status;

                    return (
                        <div className="mt-3 text-[10px] text-red-300 bg-red-500/10 p-2 rounded border border-red-500/20 flex items-center gap-2">
                            <AlertTriangle className="w-3 h-3" />
                            {errorText}
                        </div>
                    )
                }
                return null;
            })()}
        </div>
    );
}
