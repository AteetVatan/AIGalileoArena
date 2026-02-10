interface NeonSpinnerProps {
    className?: string;
}

export function NeonSpinner({ className = "h-48" }: NeonSpinnerProps) {
    return (
        <div className={`flex items-center justify-center ${className}`}>
            <div className="relative w-10 h-10">
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-cyan-400 animate-spin" />
                <div
                    className="absolute inset-1 rounded-full border-2 border-transparent border-b-purple-500 animate-spin"
                    style={{ animationDirection: "reverse", animationDuration: "0.6s" }}
                />
            </div>
        </div>
    );
}
