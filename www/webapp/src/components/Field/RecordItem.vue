<template>
  <v-layout class="flex">
    <div
      v-for="(field, index) in fields"
      :key="index"
      :class="index == fields.length - 1 ? 'flex-grow-1' : ''"
    >
      <v-text-field
        ref="input"
        v-model="field.value"
        :label="hideLabel ? '' : field.label"
        :class="hideLabel ? 'pt-0' : ''"
        :disabled="disabled"
        :readonly="readonly"
        :placeholder="required && !field.optional ? ' ' : '(optional)'"
        :hide-details="!content.length || !($v.fields.$each[index].$invalid || $v.fields[index].$invalid)"
        :error="$v.fields.$each[index].$invalid || $v.fields[index].$invalid"
        :error-messages="fieldErrorMessages(index)"
        :style="{ width: fieldWidth(index) }"
        :append-icon="index == fields.length-1 && !readonly && !disabled ? appendIcon : ''"
        @click:append="$emit('remove', $event)"
        @input="inputHandler()"
        @paste.prevent="pasteHandler($event)"
        @keydown="keydownHandler(index, $event)"
        @keyup="(e) => $emit('keyup', e)"
      />
      <span
        ref="mirror"
        aria-hidden="true"
        style="opacity: 0; position: absolute; width: auto; white-space: pre; z-index: -1"
      />
      {{ errorMessages.join(' ') }}
    </div>
  </v-layout>
</template>

<script>
import { requiredUnless } from 'vuelidate/lib/validators';

export default {
  name: 'RecordItem',
  components: {
  },
  props: {
    content: {
      type: String,
      required: true,
    },
    errorMessages: {
      type: Array,
      default: () => [],
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    required: {
      type: Boolean,
      default: true,
    },
    hideLabel: {
      type: Boolean,
      default: false,
    },
    appendIcon: {
      type: String,
      required: false,
    },
  },
  data: () => ({
    errors: {
      required: ' ',
    },
    fields: [
      { label: 'Value', validations: {} },
    ],
    value: '',
  }),
  watch: {
    content: function () {
      this.update(this.content);
    }
  },
  beforeMount() {
    // Initialize per-field value storage
    this.fields.forEach((field) => {
      this.$set(field, 'value', '');
    });

    // Update internal and graphical representation
    this.update(this.content);
  },
  validations() {
    const validations = {
      fields: {
        $each: {
          value: this.required ? { required: requiredUnless('optional') } : {},
        },
      },
    };

    validations.fields = this.fields.reduce(
      (acc, field, index) => {
        acc[index] = { value: field.validations };
        return acc;
      },
      validations.fields,
    );

    return validations;
  },
  methods: {
    fieldErrorMessages(index) {
      const fieldValidationStatus = (fields, index) => Object.keys(fields[index].value.$params).map(
        name => ({ passed: fields[index].value[name], message: this.errors[name] }),
      );

      const validationStatus = [
        ...fieldValidationStatus(this.$v.fields, index),
        ...fieldValidationStatus(this.$v.fields.$each, index),
      ];

      return validationStatus.filter(val => !val.passed).map(val => val.message || 'Invalid input.');
    },
    fieldWidth(index) {
      let ret = 'auto';
      const inputs = this.$refs.input;
      const mirrors = this.$refs.mirror;
      if (index < this.fields.length - 1 && inputs && mirrors) {
        const mirror = mirrors[index];
        while (mirror.childNodes.length) {
          mirror.removeChild(mirror.childNodes[0]);
        }

        const style = window.getComputedStyle(inputs[index].$el);
        mirror.style.border = style.getPropertyValue('border');
        mirror.style.fontSize = style.getPropertyValue('font-size');
        mirror.style.fontFamily = style.getPropertyValue('font-family');
        mirror.style.fontWeight = style.getPropertyValue('font-weight');
        mirror.style.fontStyle = style.getPropertyValue('font-style');
        mirror.style.fontFeatureSettings = style.getPropertyValue('font-feature-settings');
        mirror.style.fontKerning = style.getPropertyValue('font-kerning');
        mirror.style.fontStretch = style.getPropertyValue('font-stretch');
        mirror.style.fontVariant = style.getPropertyValue('font-variant');
        mirror.style.fontVariantCaps = style.getPropertyValue('font-variant-caps');
        mirror.style.fontVariantLigatures = style.getPropertyValue('font-variant-ligatures');
        mirror.style.fontVariantNumeric = style.getPropertyValue('font-variant-numeric');
        mirror.style.letterSpacing = style.getPropertyValue('letter-spacing');
        mirror.style.padding = style.getPropertyValue('padding');
        mirror.style.textTransform = style.getPropertyValue('text-transform');

        mirror.appendChild(document.createTextNode(`${this.fields[index].value} `));

        ret = mirror.getBoundingClientRect().width;

        mirror.removeChild(mirror.childNodes[0]);
        mirror.appendChild(document.createTextNode(`${this.fields[index].label} `));
        ret = Math.max(ret, mirror.getBoundingClientRect().width);
        ret += 'px';
      }
      return ret;
    },
    focus() {
      this.$refs.input[0].focus();
    },
    async update(value, caretPosition) {
      await this.$nextTick();

      // Right-trim if the cursor position is not after the last character
      let trimmed = value.replace(/ +$/g, '');
      const n = (trimmed.match(/ /g) || []).length;
      const diff = Math.max(0, (this.fields.length - 1) - n);
      trimmed += ' '.repeat(diff);
      if (caretPosition < trimmed.length) {
        value = trimmed;
      }

      // Only emit update event if there's news
      const dirty = (value !== this.value);
      if (dirty) {
        this.value = value;
        this.$emit('update:content', this.value);
      }

      // Always update fields as left-side fields with empty neighbor might have a trailing space
      // This case does not change the record value, but the field representation needs an update
      this.updateFields();

      if (caretPosition !== undefined) {
        await this.setPosition(caretPosition);
      }
    },
    positionAfterDelimiter(index) {
      const ref = this.$refs.input[index].$refs.input;
      return index > 0 && ref.selectionStart === 0 && ref.selectionEnd === 0;
    },
    positionBeforeDelimiter(index) {
      return index < this.fields.length - 1
        && this.$refs.input[index].$refs.input.selectionStart === this.fields[index].value.length;
    },
    keydownHandler(index, event) {
      switch (event.key) {
        case "Backspace":
          this.backspaceHandler(index, event);
          break;
        case " ":
          this.spaceHandler(index, event);
          break;
        case "End":
          this.endHandler(event);
          break;
        case "Home":
          this.homeHandler(event);
          break;
        case "ArrowLeft":
          this.leftHandler(index, event);
          break;
        case "ArrowRight":
          this.rightHandler(index, event);
          break;
        case "Delete":
          this.deleteHandler(index, event);
          break;
      }
    },
    spaceHandler(index, event) {
      if (!this.positionBeforeDelimiter(index)) {
        return;
      }

      const length = this.fields.slice(index + 1)
        .map(field => field.value.length)
        .reduce((acc, curr) => acc + curr, 0);

      if (length === 0 || this.fields[this.fields.length - 1].value.length > 0) {
        return this.rightHandler(index, event);
      }
    },
    backspaceHandler(index, event) {
      if (!this.positionAfterDelimiter(index)) {
        return;
      }

      event.preventDefault();
      const pos = this.getPosition();
      this.update(this.value.slice(0, pos - 1) + this.value.slice(pos), pos - 1);
    },
    deleteHandler(index, event) {
      if (!this.positionBeforeDelimiter(index)) {
        return;
      }

      event.preventDefault();
      const pos = this.getPosition();
      this.update(this.value.slice(0, pos) + this.value.slice(pos + 1), pos);
    },
    leftHandler(index, event) {
      if (!this.positionAfterDelimiter(index)) {
        return;
      }

      event.preventDefault();
      this.setPosition(this.getPosition() - 1);
    },
    rightHandler(index, event) {
      if (!this.positionBeforeDelimiter(index)) {
        return;
      }

      event.preventDefault();
      this.setPosition(this.getPosition() + 1);
    },
    endHandler(event) {
      event.preventDefault();
      this.setPosition(this.value.length);
    },
    homeHandler(event) {
      event.preventDefault();
      this.setPosition(0);
    },
    inputHandler() {
      const pos = this.getPosition();
      const value = this.fields.map(field => field.value).join(' ');
      this.update(value, pos);
    },
    pasteHandler(e) {
      let value = this.fields.map(field => field.value).join(' ');
      const pos = this.getPosition();
      const clipboardData = e.clipboardData.getData('text');

      // number of fields covered by this paste, minus 1 (given by number of spaces in the clipboard text, bounded from
      // above by the number of fields (minus 1) at or to the right of the caret position
      const nBeforeCaret = (value.slice(0, pos).match(/ /g) || []).length
      const n = Math.min((clipboardData.match(/ /g) || []).length, this.fields.length - 1 - nBeforeCaret);

      // Insert clipboard text and remove up to n spaces form the right
      value = value.slice(0, pos) + clipboardData + value.slice(pos);
      value = value.replace(new RegExp(` {0,${n}}$`,'g'), '');
      this.update(value, pos + clipboardData.length);
    },
    async setPosition(pos) {
      await this.$nextTick();
      let i = 0;
      while (pos > this.fields[i].value.length && i + 1 < this.fields.length) {
        pos -= this.fields[i].value.length + 1;
        i++;
      }

      this.$refs.input[i].$refs.input.setSelectionRange(pos, pos);
      this.$refs.input[i].$refs.input.focus();
    },
    getPosition() {
      let caretPosition;
      const refs = this.$refs.input;
      const dirty = refs.findIndex(ref => ref.$refs.input === document.activeElement);
      if (dirty >= 0) {
        caretPosition = refs[dirty].$refs.input.selectionStart;
        for (let i = 0; i < dirty; i++) {
          caretPosition += refs[i].$refs.input.value.length + 1;
        }
      }
      return caretPosition;
    },
    updateFields() {
      let values = this.value.split(' ');
      const last = values.slice(this.fields.length - 1).join(' ');
      values = values.slice(0, this.fields.length - 1);
      values = values.concat([last]);
      // Make sure to reset trailing fields if value does not have enough spaces
      this.fields.forEach((foo, i) => {
        this.$set(this.fields[i], 'value', values[i] || '');
      });
    },
  },
};
</script>
