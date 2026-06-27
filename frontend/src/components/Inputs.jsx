import { formatPhone } from "../lib";

/**
 * Currency input — accepts only digits and formats as "R$ 123.456,78" while typing.
 * Works "cents-first": each typed digit shifts the value (12 -> R$ 0,12 -> 1,23...).
 * `value` is a number (in reais); `onChange` receives a number (or "" when allowEmpty).
 */
export function MoneyInput({ value, onChange, allowEmpty = false, ...props }) {
  const empty = allowEmpty && (value === "" || value == null);
  const display = empty
    ? ""
    : "R$ " +
      (Number(value) || 0).toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });

  function handle(e) {
    const digits = (e.target.value.match(/\d/g) || []).join("");
    if (allowEmpty && digits === "") return onChange("");
    onChange(parseInt(digits || "0", 10) / 100);
  }

  return <input inputMode="numeric" value={display} onChange={handle} {...props} />;
}

/**
 * Phone input — accepts only digits and formats as "(99) 98888-7777" while typing.
 * `value` and `onChange` use the formatted string.
 */
export function PhoneInput({ value, onChange, ...props }) {
  return (
    <input
      inputMode="tel"
      maxLength={16}
      value={formatPhone(value)}
      onChange={(e) => onChange(formatPhone(e.target.value))}
      {...props}
    />
  );
}
