/**
 * Custom Jinjava filter: tojson
 *
 * Converts values to JSON-safe literals:
 * - null → "null"
 * - true/false → "true"/"false"
 * - strings → quoted strings
 * - numbers → numbers
 * - collections/maps → JSON representation
 *
 * Usage in templates: {{ value | tojson }}
 */
package com.alfa.sdui;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hubspot.jinjava.lib.filter.Filter;
import com.hubspot.jinjava.interpret.JinjavaInterpreter;

public class ToJsonFilter implements Filter {

    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public String getName() {
        return "tojson";
    }

    @Override
    public Object filter(Object var, JinjavaInterpreter interpreter, String... args) {
        if (var == null) {
            return "null";
        }

        if (var instanceof Boolean) {
            return var.toString(); // "true" or "false"
        }

        if (var instanceof Number) {
            return var.toString();
        }

        // For strings, arrays, maps — use Jackson serialization
        try {
            return mapper.writeValueAsString(var);
        } catch (JsonProcessingException e) {
            // Fallback: return string representation
            return "\"" + var.toString().replace("\"", "\\\"") + "\"";
        }
    }
}
