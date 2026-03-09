Use Case 1:  Demonstration of ASM TAAS Capabilities Thru Visualization for Instrument Results Domain

Create AI-ready ASM data with the speed, scale, and consistency needed to drive science.  First application – demonstrate on demand dashboard visualization of small set of ASM files from multiple sources, vendors, and instrument techniques to demonstrate efficiency gains a scientist would experience when running multiple analyses on a sample and then wanting to visualize the aggregated results to make assessments.  This is done manually now, consuming valuable scientist time not doing science, and is complicated by the across the diversity of instrumentation and software we have in laboratories that aren’t natively interoperable.

Experiment 1: 

Create ASM files from the native output files of 2 vendors of plate readers for diversity, 1 vendor of a cell counter, and 1 vendor of a solution analyzer using existing published ASM schema https://gitlab.com/allotrope-public/asm, aggregate this information vs a lab sample (knowledge graph ?) and use this to mock up a simple visualization dashboard for scientists to view these results vs the sample

 

Use Case 2:  Ensure the quality and consistency of ASM files generated at scale across the industry

ASM validation & certification service which will be essential for consistency & AI-readiness when ASMs are being created at scale across the industry

Experiment 2:

Compare above ASM files produced AWS to those provided by Merck and vs the ASM schema and report findings as a mock up of an ASM validation & certification tool.  Minimum goal – if files match (use one as reference), label the other file as Allotrope Validated or Certified as an example of how future service could work.  Stretch goal – in addition to identifying the differences and labeling, create services to update the non-conforming file to be conformant (correct it vs reference) as mock up of ASM remediation service (think of it as beginning of an automated governance processes ?)  This would just be correcting ASM file structure vs the core ASM schema.

 

Use Case 3:  Ensure ASM TAAS pipeline can operate at scale at the speed of science

Accelerate ASM creation, validation, and certification via application of AI.  Goal is >10x improvement in cycle time vs current state using accessible technology for any organization already using cloud services (e.g., democratizes access to ASM files at any scale by not for profits or for profits with turnkey solution).

Experiment 3:

TBD, but all more instrument types, amounts of data, incorporate AI to make this as fast and robust as possible and encourage broad adoption.

 

Use Case 4:  Accelerated Method Development and Simulation

Produce ASMs via above service for methods and results, aggregate in knowledge graph with sample information, provide visualizations, etc to facilitate method development decision making by assessing impact of method parameters on analysis results on demand.  ASM files can be inputs into AI-enabled software to build better method simulation or digital twin software to build more robust methods first time.

 

Use Case 5:  Process Insights and Simulation

Expand Use Case 4 to include process ASMs (e.g., output of an ELN or MES system) and aggregate as above in knowledge graph with sample, method, and result information with visualizations to facilitate process development and understanding, digital twin builds, etc.  This pipeline of harmonized ASM data across multiple data types would be fed into the knowledge graph during development (leveraging the consistent semantics provided by ontologies) to connect a living knowledge base for scientists, all happening automatically and behind the scenes.  This would transform how scientists work if data were automatically categorized and organized and could be used to generate on demand insights.   Since some data are less important than others (transactional), such a service would need the ability to label data and choose whether to populate a knowledge graph or not.