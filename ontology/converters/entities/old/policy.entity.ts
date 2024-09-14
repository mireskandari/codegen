import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvEntity } from '@vsolv/dev-kit/nest';
import { Policy } from '@wsphere/warranties/domain';
import { Column, CreateDateColumn, OneToMany, PrimaryColumn, UpdateDateColumn } from 'typeorm';
import { CoverageEntity } from '../../coverage';
import { PolicyAggregate } from '../models';

@VsolvEntity({ prefix: 'pol', name: 'warranty_policy' }, 'tenant')
export class PolicyEntity {
  @PrimaryColumn()
  id!: string;

  @Column({ nullable: true })
  referenceId!: string | null;

  @CreateDateColumn()
  created!: Date;

  @UpdateDateColumn()
  modified!: Date;

  @Column()
  policyNumber!: string;

  @Column()
  title!: string;

  @Column()
  termDuration!: number;

  @Column({ type: 'simple-enum', enum: Policy.Status })
  status!: Policy.Status;

  @OneToMany(() => CoverageEntity, cov => cov.policy)
  coverages?: CoverageEntity[];

  @Column()
  termsAndConditionsDownloadUrl!: string;

  @Column()
  ipidDownloadUrl!: string;

  toAggregate(publisher?: EventPublisher): PolicyAggregate {
    return mergeObjectContext(
      new PolicyAggregate({
        id: this.id,
        referenceId: this.referenceId,

        created: this.created,
        modified: this.modified,

        policyNumber: this.policyNumber,

        title: this.title,
        termDuration: this.termDuration,

        status: this.status,

        coverages: this.coverages?.map(cov => cov.toAggregate(publisher)) ?? undefined,
        termsAndConditionsDownloadUrl: this.termsAndConditionsDownloadUrl,
        ipidDownloadUrl: this.ipidDownloadUrl,
      }),
      publisher
    );
  }
}
