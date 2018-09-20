import logging
import os
import time
from tempfile import NamedTemporaryFile

import pandas as pd
from flask import Flask, render_template, jsonify, request, redirect, url_for, g, send_file, session, \
    render_template_string

from remus.bio.bed.beds_operations import BedsMutualOperation
from remus.bio.genes.registry import GenesDBRegistry
from remus.bio.regulatory_regions.registry import RegulatoryRegionsFilesRegistry
from remus.bio.tss.registry import TranscriptionStartSitesRegistry
from remus.processing import get_matching_genes, get_matching_tissues, BedsCollector

app = Flask(__name__)
app.secret_key = b'\xa9\xf8J\xad\x1bj\x02\x06\x12\xdf\xd9\xf2\xb1\xe9Zu'
pd.set_option('display.float_format', lambda x: '%.3f' % x)


@app.before_request
def setup_registries():
    g.genes_registry = GenesDBRegistry()
    g.tissues_registry = RegulatoryRegionsFilesRegistry()
    g.tss_registry = TranscriptionStartSitesRegistry()


@app.after_request
def teardown_registries(response):
    g.genes_registry.teardown_registry()
    return response


@app.route("/")
def index():
    return render_template('index.html', title="Remus")


@app.route("/api/genes")
def genes():
    genome_name = request.args.get("genome", None)
    pattern = request.args.get("pattern", None)
    limit = request.args.get("limit", default=10, type=int)
    genes_names = get_matching_genes(pattern, genome_name, limit)
    return jsonify(genes_names)


@app.route("/api/tissues")
def tissues():
    pattern = request.args.get("pattern", None)
    limit = request.args.get("limit", default=0, type=int)
    tissues_names = get_matching_tissues(pattern, limit)
    return jsonify(tissues_names)


@app.route("/api/perform", methods=["POST"])
def perform():
    try:
        start_time = time.time()
        params = get_perform_params()
        collected_beds_map = BedsCollector(params).collect_bed_files()
        collected_beds_without_categories = [bed for beds_list in collected_beds_map.values() for bed in beds_list]
        if len(collected_beds_without_categories) == 1:
            collected_beds_without_categories += collected_beds_without_categories
        final_processor = BedsMutualOperation(collected_beds_without_categories, operation="union")
        tmp_file_path = save_as_tmp(final_processor.result)
        session["last_result"] = tmp_file_path.name
        end_time = (time.time() - start_time)
        return return_summary(final_processor, end_time)
    except Exception as e:
        logging.exception("Error occurred, details:")
        return "Error occurred"


def save_as_tmp(result):
    tmp_file = NamedTemporaryFile(suffix="bed", delete=False)
    result.saveas(tmp_file.name)
    return tmp_file


@app.route("/api/download_last")
def download_last():
    last_result_path = session.get("last_result", None)
    if last_result_path and os.path.exists(last_result_path):
        return send_file(last_result_path, mimetype="text/bed", attachment_filename='result.bed', as_attachment=True)
    else:
        return "", 202


def return_summary(processor, time_elapsed):
    summary_data = [
        ("Time elapsed (s)", round(time_elapsed, 6)),
        ("No. features", int(len(processor.result))),
        ("No. base pairs", int(processor.result.total_coverage()))
    ]
    template = """
    <table border="1" class="table-bordered table-striped table-hover">
        {% for header, value in data %}
           <tr>
                <th> {{ header }} </th>
                <td> {{ value }} </td>
           </tr>
        {% endfor %}
    </table>
    """
    return render_template_string(template, data=summary_data)


def get_perform_params():
    collected_parameters = {}
    collected_parameters.update(get_single_value_params())
    collected_parameters.update(get_multiple_values_params())
    return collected_parameters


def get_single_value_params():
    single_value_params = ["genome",
                           "transcription-fantom5-used",
                           "enhancers-fantom5-used",
                           "enhancers-encode-used",
                           "accessible-chromatin-encode-used",
                           "transcription-fantom5-range",
                           "enhancers-fantom5-range",
                           "enhancers-encode-range",
                           "accessible-chromatin-encode-range",
                           "transcription-fantom5-kbs-upstream",
                           "transcription-fantom5-kbs-downstream",
                           "enhancers-fantom5-kbs-upstream",
                           "enhancers-fantom5-kbs-downstream",
                           "enhancers-encode-kbs-upstream",
                           "enhancers-encode-kbs-downstream",
                           "accessible-chromatin-encode-kbs-upstream",
                           "accessible-chromatin-encode-kbs-downstream"
                           ]

    params_map = {p: request.form.get(p, None) for p in single_value_params}
    #params_map["transcription-fantom5-range"] = "any"  # Not used currently but generally required parameter
    return params_map


def get_multiple_values_params():
    multiple_values_params = ["genes", "tissues"]
    return {p: request.form.getlist(p, None) for p in multiple_values_params}


@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='img/remus.ico'), code=302)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404
