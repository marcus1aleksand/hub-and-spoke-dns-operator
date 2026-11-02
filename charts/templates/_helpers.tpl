{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "dns-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "dns-operator.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create the chart version.
*/}}
{{- define "dns-operator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "dns-operator.labels" -}}
helm.sh/chart: {{ include "dns-operator.chart" . }}
{{ include "dns-operator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "dns-operator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dns-operator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "dns-operator.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "dns-operator.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
Replica count for the deployment.
The "default" function cannot be used here: it treats 0 as an empty value, so
an explicit replicaCount of 0 would silently be replaced by the fallback.
*/}}
{{- define "dns-operator.replicaCount" -}}
{{- if kindIs "invalid" .Values.replicaCount -}}
1
{{- else -}}
{{- .Values.replicaCount -}}
{{- end -}}
{{- end -}}

{{/*
Whether the service account token should be automounted.
The "default" function cannot be used here either: false is an empty value for
it, so an explicit automountServiceAccountToken: false would silently be
turned back into true.
*/}}
{{- define "dns-operator.automountServiceAccountToken" -}}
{{- $deployment := .Values.deployment | default dict -}}
{{- $value := index $deployment "automountServiceAccountToken" -}}
{{- if kindIs "bool" $value -}}
{{- $value -}}
{{- else -}}
true
{{- end -}}
{{- end -}}