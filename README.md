# Next generation acron service

Acron is a centralised, authenticated service which allows users to periodically execute tasks on arbitrary target nodes to which they have access.

This project contains client and server tools, including different open source backend examples, serving as a replacement for the legacy acron service.

## Redesign

The goal of the redesign was to get rid of legacy protocols such as ARC, as well as dependencies on AFS, which is deprecated.

The client tools are used to

- manage user credentials
- manage user authenticated cron entries

## Requirements

- Provide the same functionality as the legacy acron service
- Eliminate legacy home grown components and base it on free Open Source tools
- Improve security
- Improve redundancy of the service

## Related

- [Acron user docs](https://acrondocs.web.cern.ch/)
