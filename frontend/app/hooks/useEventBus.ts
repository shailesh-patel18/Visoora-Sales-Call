import { useEffect } from 'react';
import { useAuthStore } from '../store';

export function useEventBus(onEvent: (event: any) => void) {
    const { token, tenantId } = useAuthStore();

    useEffect(() => {
        if (!token || !tenantId) return;

        // Native EventSource doesn't support custom headers (like Authorization: Bearer).
        // Since Visoora APIs expect the token, we can pass it as a query parameter.
        const url = `/api/events/stream?token=${token}`;
        const eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
            try {
                const parsedData = JSON.parse(event.data);
                if (parsedData.event_type !== 'connected') {
                    onEvent(parsedData);
                }
            } catch (err) {
                console.error("Error parsing event bus message", err);
            }
        };

        eventSource.onerror = (err) => {
            console.error("EventBus connection error", err);
        };

        return () => {
            eventSource.close();
        };
    }, [token, tenantId, onEvent]);
}
