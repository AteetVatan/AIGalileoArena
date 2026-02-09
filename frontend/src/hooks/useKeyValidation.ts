"use client";

import { useState, useCallback, useEffect } from "react";
import { api } from "@/lib/api";
import { useAvailableKeys, useValidateKeys } from "@/lib/queries";
import type { KeyValidationResult, KeyValidationStatus } from "@/lib/types";
import { AVAILABLE_MODELS } from "@/lib/constants";

export function useKeyValidation() {
    const { data: availableKeysData } = useAvailableKeys();
    const availableKeys = new Set(availableKeysData?.available_keys || []);

    const {
        data: validationData,
        refetch: refreshValidation,
        isLoading: validationLoading,
        isError: validationError
    } = useValidateKeys();

    const keyValidation = new Map(Object.entries(validationData || {}));

    const isModelAvailable = useCallback(
        (model: (typeof AVAILABLE_MODELS)[0]) => {
            if (!availableKeysData) return true; // Assume available while loading
            return availableKeys.has(model.api_key_env);
        },
        [availableKeys, availableKeysData]
    );

    const getValidationStatus = useCallback(
        (model: (typeof AVAILABLE_MODELS)[0]): KeyValidationStatus | null => {
            const validation = keyValidation.get(model.api_key_env);
            return validation?.status || null;
        },
        [keyValidation]
    );

    const isModelDisabled = useCallback(
        (model: (typeof AVAILABLE_MODELS)[0]): boolean => {
            if (!isModelAvailable(model)) return true;
            const status = getValidationStatus(model);
            return (
                status === "INVALID_KEY" || status === "NO_FUNDS_OR_BUDGET"
            );
        },
        [isModelAvailable, getValidationStatus]
    );

    return {
        availableKeys,
        keyValidation,
        validationLoading,
        validationError,
        refreshValidation,
        isModelAvailable,
        getValidationStatus,
        isModelDisabled,
    };
}
