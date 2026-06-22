FROM odoo:17.0

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY ./addons /mnt/extra-addons

RUN chown -R odoo:odoo /mnt/extra-addons

USER odoo
